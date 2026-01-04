"""
MongoDB Persistence Layer for OVN Store Chatbot
Handles chat session storage, user memory, and analytics
"""
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pymongo import MongoClient, DESCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MONGO_URI, DATABASE_NAME


class MongoDBConnection:
    """Singleton MongoDB connection manager"""
    _instance = None
    _client = None
    _db = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def connect(self) -> bool:
        """Establish MongoDB connection"""
        if self._client is not None:
            return True

        try:
            self._client = MongoClient(
                MONGO_URI,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000
            )
            # Test connection
            self._client.admin.command('ping')
            self._db = self._client[DATABASE_NAME]
            print(f"MongoDB connected: {DATABASE_NAME}")
            return True
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            print(f"MongoDB connection failed: {e}")
            self._client = None
            self._db = None
            return False

    @property
    def db(self):
        """Get database instance"""
        if self._db is None:
            self.connect()
        return self._db

    @property
    def is_connected(self) -> bool:
        """Check if connected to MongoDB"""
        return self._db is not None


# Global connection instance
mongo_connection = MongoDBConnection()


class ChatSessionStore:
    """
    Handles CRUD operations for chat sessions in MongoDB.
    Collection: chat_sessions
    """

    def __init__(self):
        self.collection_name = 'chat_sessions'

    @property
    def collection(self):
        db = mongo_connection.db
        if db is not None:
            return db[self.collection_name]
        return None

    def save_session(self, session_data: Dict) -> bool:
        """
        Save or update a chat session.
        Uses upsert to create if not exists.
        """
        if self.collection is None:
            return False

        try:
            session_id = session_data.get('session_id')
            if not session_id:
                return False

            # Prepare document
            doc = {
                'session_id': session_id,
                'phone': session_data.get('user_phone'),
                'user_id': session_data.get('user_id'),
                'is_active': session_data.get('is_active', True),
                'admin_handling': session_data.get('admin_handling', False),
                'admin_id': session_data.get('admin_id'),
                'state': session_data.get('state', 'idle'),
                'state_context': session_data.get('state_context', {}),
                'user_info': {
                    'name': session_data.get('user_name'),
                    'phone': session_data.get('user_phone'),
                    'email': session_data.get('user_email'),
                    'location': session_data.get('user_location'),
                    'landmark': session_data.get('user_landmark')
                },
                'conversation_history': session_data.get('conversation_history', []),
                'selected_products': session_data.get('selected_products', []),
                'preferences': session_data.get('preferences', {}),
                'stats': session_data.get('stats', {}),
                'created_at': session_data.get('created_at', datetime.now()),
                'last_activity': datetime.now(),
                'updated_at': datetime.now()
            }

            self.collection.update_one(
                {'session_id': session_id},
                {'$set': doc},
                upsert=True
            )
            return True

        except Exception as e:
            print(f"Error saving session: {e}")
            return False

    def load_session(self, session_id: str) -> Optional[Dict]:
        """Load a session by session_id"""
        if self.collection is None:
            return None

        try:
            doc = self.collection.find_one({'session_id': session_id})
            if doc:
                doc['_id'] = str(doc['_id'])  # Convert ObjectId to string
                return doc
            return None
        except Exception as e:
            print(f"Error loading session: {e}")
            return None

    def find_sessions_by_phone(self, phone: str, limit: int = 10) -> List[Dict]:
        """Find all sessions for a phone number"""
        if self.collection is None:
            return []

        try:
            cursor = self.collection.find(
                {'phone': phone}
            ).sort('last_activity', DESCENDING).limit(limit)

            sessions = []
            for doc in cursor:
                doc['_id'] = str(doc['_id'])
                sessions.append(doc)
            return sessions
        except Exception as e:
            print(f"Error finding sessions by phone: {e}")
            return []

    def find_sessions_by_user_id(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Find all sessions for a user ID"""
        if self.collection is None:
            return []

        try:
            cursor = self.collection.find(
                {'user_id': user_id}
            ).sort('last_activity', DESCENDING).limit(limit)

            sessions = []
            for doc in cursor:
                doc['_id'] = str(doc['_id'])
                sessions.append(doc)
            return sessions
        except Exception as e:
            print(f"Error finding sessions by user_id: {e}")
            return []

    def get_active_sessions(self, limit: int = 50) -> List[Dict]:
        """Get all active sessions for admin view"""
        if self.collection is None:
            return []

        try:
            # Sessions active in last 30 minutes
            cutoff = datetime.now() - timedelta(minutes=30)
            cursor = self.collection.find(
                {'last_activity': {'$gte': cutoff}, 'is_active': True}
            ).sort('last_activity', DESCENDING).limit(limit)

            sessions = []
            for doc in cursor:
                doc['_id'] = str(doc['_id'])
                sessions.append(doc)
            return sessions
        except Exception as e:
            print(f"Error getting active sessions: {e}")
            return []

    def get_all_sessions(self, filters: Dict = None, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get sessions with optional filters for admin panel"""
        if self.collection is None:
            return []

        try:
            query = {}
            if filters:
                if filters.get('phone'):
                    query['phone'] = {'$regex': filters['phone'], '$options': 'i'}
                if filters.get('date_from'):
                    query['created_at'] = {'$gte': filters['date_from']}
                if filters.get('date_to'):
                    if 'created_at' in query:
                        query['created_at']['$lte'] = filters['date_to']
                    else:
                        query['created_at'] = {'$lte': filters['date_to']}
                if filters.get('admin_handling') is not None:
                    query['admin_handling'] = filters['admin_handling']

            cursor = self.collection.find(query).sort(
                'last_activity', DESCENDING
            ).skip(offset).limit(limit)

            sessions = []
            for doc in cursor:
                doc['_id'] = str(doc['_id'])
                sessions.append(doc)
            return sessions
        except Exception as e:
            print(f"Error getting all sessions: {e}")
            return []

    def count_sessions(self, filters: Dict = None) -> int:
        """Count sessions with optional filters"""
        if self.collection is None:
            return 0

        try:
            query = {}
            if filters:
                if filters.get('phone'):
                    query['phone'] = {'$regex': filters['phone'], '$options': 'i'}
            return self.collection.count_documents(query)
        except Exception as e:
            print(f"Error counting sessions: {e}")
            return 0

    def add_message(self, session_id: str, message: Dict) -> bool:
        """Add a message to session's conversation history"""
        if self.collection is None:
            return False

        try:
            self.collection.update_one(
                {'session_id': session_id},
                {
                    '$push': {'conversation_history': message},
                    '$set': {'last_activity': datetime.now()},
                    '$inc': {'stats.total_messages': 1}
                }
            )
            return True
        except Exception as e:
            print(f"Error adding message: {e}")
            return False

    def set_admin_handling(self, session_id: str, admin_id: int, handling: bool) -> bool:
        """Set admin handling status for a session"""
        if self.collection is None:
            return False

        try:
            self.collection.update_one(
                {'session_id': session_id},
                {
                    '$set': {
                        'admin_handling': handling,
                        'admin_id': admin_id if handling else None,
                        'last_activity': datetime.now()
                    }
                }
            )
            return True
        except Exception as e:
            print(f"Error setting admin handling: {e}")
            return False

    def mark_inactive(self, session_id: str) -> bool:
        """Mark a session as inactive"""
        if self.collection is None:
            return False

        try:
            self.collection.update_one(
                {'session_id': session_id},
                {'$set': {'is_active': False, 'updated_at': datetime.now()}}
            )
            return True
        except Exception as e:
            print(f"Error marking session inactive: {e}")
            return False

    def cleanup_old_sessions(self, days: int = 30) -> int:
        """Clean up sessions older than specified days"""
        if self.collection is None:
            return 0

        try:
            cutoff = datetime.now() - timedelta(days=days)
            result = self.collection.delete_many({'last_activity': {'$lt': cutoff}})
            return result.deleted_count
        except Exception as e:
            print(f"Error cleaning up sessions: {e}")
            return 0


class UserMemory:
    """
    Handles persistent user memory across sessions.
    Remembers user info by phone number or user ID.
    Collection: user_memory
    """

    def __init__(self):
        self.collection_name = 'user_memory'

    @property
    def collection(self):
        db = mongo_connection.db
        if db is not None:
            return db[self.collection_name]
        return None

    def get_by_phone(self, phone: str) -> Optional[Dict]:
        """Get user memory by phone number"""
        if self.collection is None or not phone:
            return None

        try:
            doc = self.collection.find_one({'phone': phone})
            if doc:
                doc['_id'] = str(doc['_id'])
            return doc
        except Exception as e:
            print(f"Error getting user memory by phone: {e}")
            return None

    def get_by_user_id(self, user_id: int) -> Optional[Dict]:
        """Get user memory by Django user ID"""
        if self.collection is None or not user_id:
            return None

        try:
            doc = self.collection.find_one({'user_id': user_id})
            if doc:
                doc['_id'] = str(doc['_id'])
            return doc
        except Exception as e:
            print(f"Error getting user memory by user_id: {e}")
            return None

    def get_by_identifier(self, identifier: str) -> Optional[Dict]:
        """Get user memory by phone or user_id"""
        if self.collection is None or not identifier:
            return None

        # Try phone first
        if identifier.isdigit() and len(identifier) == 10:
            result = self.get_by_phone(identifier)
            if result:
                return result

        # Try as user_id
        try:
            user_id = int(identifier)
            return self.get_by_user_id(user_id)
        except ValueError:
            pass

        return None

    def update(self, phone: str = None, user_id: int = None, data: Dict = None) -> bool:
        """Update or create user memory"""
        if self.collection is None or (not phone and not user_id):
            return False

        try:
            # Build query
            if phone:
                query = {'phone': phone}
            else:
                query = {'user_id': user_id}

            # Prepare update
            update_data = data or {}
            update_data['updated_at'] = datetime.now()

            self.collection.update_one(
                query,
                {
                    '$set': update_data,
                    '$setOnInsert': {'created_at': datetime.now()}
                },
                upsert=True
            )
            return True
        except Exception as e:
            print(f"Error updating user memory: {e}")
            return False

    def remember_user_info(self, phone: str, name: str = None, email: str = None,
                          location: str = None, landmark: str = None) -> bool:
        """Convenience method to remember user info"""
        data = {}
        if name:
            data['name'] = name
        if email:
            data['email'] = email
        if location:
            data['preferred_location'] = location
        if landmark:
            data['preferred_landmark'] = landmark

        return self.update(phone=phone, data=data)

    def record_order(self, phone: str, order_id: str, order_total: float,
                    category: str = None) -> bool:
        """Record an order for the user"""
        if self.collection is None or not phone:
            return False

        try:
            update = {
                '$inc': {'total_orders': 1, 'total_spent': order_total},
                '$set': {
                    'last_order_id': order_id,
                    'last_order_date': datetime.now(),
                    'updated_at': datetime.now()
                }
            }

            if category:
                update['$addToSet'] = {'categories_interested': category}

            self.collection.update_one(
                {'phone': phone},
                update,
                upsert=True
            )
            return True
        except Exception as e:
            print(f"Error recording order: {e}")
            return False

    def get_order_history_summary(self, phone: str) -> Dict:
        """Get order history summary for recommendations"""
        memory = self.get_by_phone(phone)
        if memory:
            return {
                'total_orders': memory.get('total_orders', 0),
                'total_spent': memory.get('total_spent', 0),
                'categories_interested': memory.get('categories_interested', []),
                'last_order_date': memory.get('last_order_date')
            }
        return {'total_orders': 0, 'total_spent': 0, 'categories_interested': []}


class AnalyticsStore:
    """
    Handles chat analytics aggregation and storage.
    Collection: chat_analytics
    """

    def __init__(self):
        self.collection_name = 'chat_analytics'
        self.session_store = ChatSessionStore()

    @property
    def collection(self):
        db = mongo_connection.db
        if db is not None:
            return db[self.collection_name]
        return None

    def record_event(self, event_type: str, session_id: str,
                    intent: str = None, metadata: Dict = None) -> bool:
        """Record an analytics event"""
        if self.collection is None:
            return False

        try:
            doc = {
                'event_type': event_type,
                'session_id': session_id,
                'intent': intent,
                'metadata': metadata or {},
                'timestamp': datetime.now(),
                'hour': datetime.now().hour,
                'date': datetime.now().date().isoformat()
            }
            self.collection.insert_one(doc)
            return True
        except Exception as e:
            print(f"Error recording event: {e}")
            return False

    def get_daily_summary(self, date: datetime = None) -> Dict:
        """Get analytics summary for a specific date"""
        if self.collection is None:
            return {}

        date = date or datetime.now()
        date_str = date.date().isoformat()

        try:
            # Get session stats
            sessions_collection = mongo_connection.db['chat_sessions']
            start_of_day = datetime.combine(date.date(), datetime.min.time())
            end_of_day = datetime.combine(date.date(), datetime.max.time())

            total_sessions = sessions_collection.count_documents({
                'created_at': {'$gte': start_of_day, '$lte': end_of_day}
            })

            # Get intent distribution
            intent_pipeline = [
                {'$match': {'date': date_str}},
                {'$group': {'_id': '$intent', 'count': {'$sum': 1}}},
                {'$sort': {'count': -1}}
            ]
            intent_results = list(self.collection.aggregate(intent_pipeline))
            intents = {r['_id']: r['count'] for r in intent_results if r['_id']}

            # Get hourly distribution
            hourly_pipeline = [
                {'$match': {'date': date_str}},
                {'$group': {'_id': '$hour', 'count': {'$sum': 1}}},
                {'$sort': {'_id': 1}}
            ]
            hourly_results = list(self.collection.aggregate(hourly_pipeline))
            hourly = {r['_id']: r['count'] for r in hourly_results}

            # Get orders from chat
            orders_from_chat = self.collection.count_documents({
                'date': date_str,
                'event_type': 'order_placed'
            })

            return {
                'date': date_str,
                'total_sessions': total_sessions,
                'total_events': self.collection.count_documents({'date': date_str}),
                'intents': intents,
                'hourly_distribution': hourly,
                'orders_from_chat': orders_from_chat,
                'conversion_rate': round(
                    (orders_from_chat / total_sessions * 100) if total_sessions > 0 else 0, 2
                )
            }
        except Exception as e:
            print(f"Error getting daily summary: {e}")
            return {}

    def get_top_intents(self, days: int = 7, limit: int = 10) -> List[Dict]:
        """Get top intents over a period"""
        if self.collection is None:
            return []

        try:
            cutoff = datetime.now() - timedelta(days=days)
            pipeline = [
                {'$match': {'timestamp': {'$gte': cutoff}, 'intent': {'$ne': None}}},
                {'$group': {'_id': '$intent', 'count': {'$sum': 1}}},
                {'$sort': {'count': -1}},
                {'$limit': limit}
            ]
            results = list(self.collection.aggregate(pipeline))
            return [{'intent': r['_id'], 'count': r['count']} for r in results]
        except Exception as e:
            print(f"Error getting top intents: {e}")
            return []

    def get_peak_hours(self, days: int = 7) -> List[Dict]:
        """Get peak activity hours"""
        if self.collection is None:
            return []

        try:
            cutoff = datetime.now() - timedelta(days=days)
            pipeline = [
                {'$match': {'timestamp': {'$gte': cutoff}}},
                {'$group': {'_id': '$hour', 'count': {'$sum': 1}}},
                {'$sort': {'_id': 1}}
            ]
            results = list(self.collection.aggregate(pipeline))
            return [{'hour': r['_id'], 'count': r['count']} for r in results]
        except Exception as e:
            print(f"Error getting peak hours: {e}")
            return []

    def get_conversion_stats(self, days: int = 7) -> Dict:
        """Get conversion statistics"""
        if self.collection is None:
            return {}

        try:
            cutoff = datetime.now() - timedelta(days=days)

            # Total sessions
            sessions_collection = mongo_connection.db['chat_sessions']
            total_sessions = sessions_collection.count_documents({
                'created_at': {'$gte': cutoff}
            })

            # Orders from chat
            orders_from_chat = self.collection.count_documents({
                'timestamp': {'$gte': cutoff},
                'event_type': 'order_placed'
            })

            # Support tickets
            support_tickets = self.collection.count_documents({
                'timestamp': {'$gte': cutoff},
                'event_type': 'support_ticket'
            })

            return {
                'total_sessions': total_sessions,
                'orders_from_chat': orders_from_chat,
                'support_tickets': support_tickets,
                'conversion_rate': round(
                    (orders_from_chat / total_sessions * 100) if total_sessions > 0 else 0, 2
                ),
                'period_days': days
            }
        except Exception as e:
            print(f"Error getting conversion stats: {e}")
            return {}


# Convenience function to get stores
def get_session_store() -> ChatSessionStore:
    return ChatSessionStore()


def get_user_memory() -> UserMemory:
    return UserMemory()


def get_analytics_store() -> AnalyticsStore:
    return AnalyticsStore()


# Initialize connection on import
mongo_connection.connect()
