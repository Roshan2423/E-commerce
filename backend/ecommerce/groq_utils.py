"""
Groq API Usage Utilities
Fetches rate limit info from Groq API
"""
import os
import json
import time
from pathlib import Path
from groq import Groq
from django.conf import settings

# Cache file for storing usage data
CACHE_FILE = Path(settings.BASE_DIR) / 'groq_usage_cache.json'
CACHE_DURATION = 60  # seconds


def get_groq_api_key():
    """Get Groq API key from environment or settings"""
    return os.getenv('GROQ_API_KEY', getattr(settings, 'GROQ_API_KEY', ''))


def get_groq_usage():
    """
    Get Groq API usage/rate limit info.
    Makes a minimal API call to check the rate limits.
    Caches the result for 60 seconds to avoid unnecessary API calls.
    """
    # Check cache first
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, 'r') as f:
                cache_data = json.load(f)
                if time.time() - cache_data.get('timestamp', 0) < CACHE_DURATION:
                    return cache_data.get('usage', {})
        except (json.JSONDecodeError, IOError):
            pass

    api_key = get_groq_api_key()
    if not api_key:
        return {
            'available': False,
            'error': 'No API key configured',
            'remaining_requests': 0,
            'remaining_tokens': 0,
            'limit_requests': 0,
            'limit_tokens': 0
        }

    try:
        client = Groq(api_key=api_key)

        # Make a minimal API call to get rate limit headers
        # Using a very short prompt to minimize token usage
        response = client.chat.completions.with_raw_response.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=1
        )

        # Extract rate limit info from headers
        headers = response.headers

        usage_data = {
            'available': True,
            'remaining_requests': int(headers.get('x-ratelimit-remaining-requests', 0)),
            'remaining_tokens': int(headers.get('x-ratelimit-remaining-tokens', 0)),
            'limit_requests': int(headers.get('x-ratelimit-limit-requests', 30)),
            'limit_tokens': int(headers.get('x-ratelimit-limit-tokens', 30000)),
            'reset_requests': headers.get('x-ratelimit-reset-requests', ''),
            'reset_tokens': headers.get('x-ratelimit-reset-tokens', ''),
            'model': 'llama-3.1-8b-instant',
            'last_checked': time.strftime('%H:%M:%S')
        }

        # Calculate percentages
        if usage_data['limit_requests'] > 0:
            usage_data['requests_percent'] = round(
                (usage_data['remaining_requests'] / usage_data['limit_requests']) * 100
            )
        else:
            usage_data['requests_percent'] = 0

        if usage_data['limit_tokens'] > 0:
            usage_data['tokens_percent'] = round(
                (usage_data['remaining_tokens'] / usage_data['limit_tokens']) * 100
            )
        else:
            usage_data['tokens_percent'] = 0

        # Cache the result
        cache_data = {
            'timestamp': time.time(),
            'usage': usage_data
        }
        try:
            with open(CACHE_FILE, 'w') as f:
                json.dump(cache_data, f)
        except IOError:
            pass

        return usage_data

    except Exception as e:
        error_data = {
            'available': False,
            'error': str(e),
            'remaining_requests': 0,
            'remaining_tokens': 0,
            'limit_requests': 30,
            'limit_tokens': 30000,
            'requests_percent': 0,
            'tokens_percent': 0
        }
        return error_data


def format_token_count(count):
    """Format token count for display (e.g., 28.5K)"""
    if count >= 1000:
        return f"{count / 1000:.1f}K"
    return str(count)
