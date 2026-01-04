"""
Chat Analytics Module
MongoDB aggregations for chat statistics and insights
"""
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pymongo import MongoClient
from decouple import config


def get_mongodb_client():
    """Get MongoDB client"""
    mongo_uri = config('MONGODB_URI', default='mongodb://localhost:27017/')
    return MongoClient(mongo_uri)


def get_chat_database():
    """Get chat database"""
    client = get_mongodb_client()
    db_name = config('MONGODB_CHAT_DB', default='ovn_chatbot')
    return client[db_name]


class ChatAnalytics:
    """Analytics for chat sessions"""

    def __init__(self):
        self.db = get_chat_database()
        self.sessions = self.db['chat_sessions']
        self.analytics = self.db['chat_analytics']

    def get_sessions_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get summary of chat sessions"""
        cutoff = datetime.now() - timedelta(days=days)

        pipeline = [
            {'$match': {'created_at': {'$gte': cutoff}}},
            {'$group': {
                '_id': None,
                'total_sessions': {'$sum': 1},
                'active_sessions': {
                    '$sum': {'$cond': [{'$eq': ['$is_active', True]}, 1, 0]}
                },
                'admin_handled': {
                    '$sum': {'$cond': [{'$eq': ['$admin_handling', True]}, 1, 0]}
                },
                'avg_messages': {'$avg': {'$size': {'$ifNull': ['$conversation_history', []]}}}
            }}
        ]

        result = list(self.sessions.aggregate(pipeline))
        if result:
            return {
                'total_sessions': result[0].get('total_sessions', 0),
                'active_sessions': result[0].get('active_sessions', 0),
                'admin_handled': result[0].get('admin_handled', 0),
                'avg_messages': round(result[0].get('avg_messages', 0), 1)
            }

        return {
            'total_sessions': 0,
            'active_sessions': 0,
            'admin_handled': 0,
            'avg_messages': 0
        }

    def get_daily_stats(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get daily chat statistics"""
        cutoff = datetime.now() - timedelta(days=days)

        pipeline = [
            {'$match': {'created_at': {'$gte': cutoff}}},
            {'$group': {
                '_id': {
                    '$dateToString': {
                        'format': '%Y-%m-%d',
                        'date': '$created_at'
                    }
                },
                'sessions': {'$sum': 1},
                'messages': {'$sum': {'$size': {'$ifNull': ['$conversation_history', []]}}}
            }},
            {'$sort': {'_id': 1}}
        ]

        result = list(self.sessions.aggregate(pipeline))
        return [
            {
                'date': r['_id'],
                'sessions': r['sessions'],
                'messages': r['messages']
            }
            for r in result
        ]

    def get_top_intents(self, days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most common intents"""
        cutoff = datetime.now() - timedelta(days=days)

        pipeline = [
            {'$match': {'timestamp': {'$gte': cutoff}}},
            {'$group': {
                '_id': '$intent',
                'count': {'$sum': 1}
            }},
            {'$sort': {'count': -1}},
            {'$limit': limit}
        ]

        result = list(self.analytics.aggregate(pipeline))
        return [
            {
                'intent': r['_id'] or 'unknown',
                'count': r['count']
            }
            for r in result
        ]

    def get_peak_hours(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get activity by hour of day"""
        cutoff = datetime.now() - timedelta(days=days)

        pipeline = [
            {'$match': {'timestamp': {'$gte': cutoff}}},
            {'$group': {
                '_id': {'$hour': '$timestamp'},
                'count': {'$sum': 1}
            }},
            {'$sort': {'_id': 1}}
        ]

        result = list(self.analytics.aggregate(pipeline))

        # Fill in all hours
        hours_data = {i: 0 for i in range(24)}
        for r in result:
            hours_data[r['_id']] = r['count']

        return [
            {'hour': h, 'count': c}
            for h, c in sorted(hours_data.items())
        ]

    def get_conversion_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get conversation to order conversion stats"""
        cutoff = datetime.now() - timedelta(days=days)

        # Total sessions
        total_sessions = self.sessions.count_documents({
            'created_at': {'$gte': cutoff}
        })

        # Sessions with orders (assuming order_placed in analytics)
        order_events = self.analytics.count_documents({
            'timestamp': {'$gte': cutoff},
            'event_type': 'order_placed'
        })

        conversion_rate = (order_events / total_sessions * 100) if total_sessions > 0 else 0

        return {
            'total_sessions': total_sessions,
            'orders_placed': order_events,
            'conversion_rate': round(conversion_rate, 1)
        }

    def get_session_list(
        self,
        filters: Dict = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get paginated session list"""
        query = filters or {}

        cursor = self.sessions.find(query).sort('last_activity', -1).skip(offset).limit(limit)

        sessions = []
        for doc in cursor:
            sessions.append({
                'session_id': doc.get('session_id', ''),
                'user_name': doc.get('user_name') or doc.get('user_info', {}).get('name', 'Anonymous'),
                'user_phone': doc.get('user_phone') or doc.get('user_info', {}).get('phone', ''),
                'state': doc.get('state', 'idle'),
                'is_active': doc.get('is_active', False),
                'admin_handling': doc.get('admin_handling', False),
                'message_count': len(doc.get('conversation_history', [])),
                'created_at': doc.get('created_at'),
                'last_activity': doc.get('last_activity')
            })

        return sessions

    def get_session_count(self, filters: Dict = None) -> int:
        """Get total session count"""
        query = filters or {}
        return self.sessions.count_documents(query)

    def get_session_detail(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get full session detail"""
        doc = self.sessions.find_one({'session_id': session_id})
        if doc:
            # Convert ObjectId to string
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])
            return doc
        return None

    def get_recent_messages(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent messages across all sessions"""
        pipeline = [
            {'$unwind': '$conversation_history'},
            {'$sort': {'conversation_history.timestamp': -1}},
            {'$limit': limit},
            {'$project': {
                'session_id': 1,
                'user_name': 1,
                'message': '$conversation_history'
            }}
        ]

        result = list(self.sessions.aggregate(pipeline))
        return [
            {
                'session_id': r.get('session_id', ''),
                'user_name': r.get('user_name', 'Anonymous'),
                'role': r.get('message', {}).get('role', ''),
                'content': r.get('message', {}).get('content', ''),
                'timestamp': r.get('message', {}).get('timestamp', '')
            }
            for r in result
        ]

    def get_response_times(self, days: int = 7) -> Dict[str, Any]:
        """Get average response time metrics"""
        # This would require tracking response times in analytics
        # For now, return placeholder
        return {
            'avg_response_time': 0,
            'min_response_time': 0,
            'max_response_time': 0
        }


# Global analytics instance
_analytics: Optional[ChatAnalytics] = None


def get_chat_analytics() -> ChatAnalytics:
    """Get or create analytics instance"""
    global _analytics
    if _analytics is None:
        _analytics = ChatAnalytics()
    return _analytics
