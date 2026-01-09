from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.middleware.csrf import get_token
import json

User = get_user_model()


@csrf_exempt
@require_POST
def api_login(request):
    """API endpoint for frontend login"""
    try:
        data = json.loads(request.body)
        username = data.get('username', '').strip()
        password = data.get('password', '')

        if not username or not password:
            return JsonResponse({
                'success': False,
                'error': 'Username/email and password are required'
            }, status=400)

        # Try to find user by username or email
        try:
            # First try by username
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                # Try by email
                user = User.objects.get(email=username)
            if user.check_password(password):
                # Manual login since authenticate() fails with Djongo
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user)
                
                # Force session save to ensure cookie is set
                request.session.save()
                
                # Determine redirect URL based on user role
                if user.is_staff or user.is_superuser:
                    redirect_url = '/dashboard/'
                    user_type = 'admin'
                else:
                    redirect_url = '/'
                    user_type = 'customer'
                
                response = JsonResponse({
                    'success': True,
                    'message': f'Welcome back, {user.get_full_name() or user.username}!',
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'is_staff': user.is_staff,
                        'is_superuser': user.is_superuser,
                        'user_type': user_type
                    },
                    'redirect_url': redirect_url
                })

                return response
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid username/email or password'
                }, status=401)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Invalid username/email or password'
            }, status=401)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Login failed. Please try again.'
        }, status=500)


@csrf_exempt
@require_POST 
def api_logout(request):
    """API endpoint for frontend logout"""
    try:
        logout(request)
        return JsonResponse({
            'success': True,
            'message': 'You have been logged out successfully.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Logout failed'
        }, status=500)


def api_auth_status(request):
    """Check current authentication status"""
    if request.user.is_authenticated:
        user_type = 'admin' if (request.user.is_staff or request.user.is_superuser) else 'customer'

        # Check if user is a vendor
        has_vendor = hasattr(request.user, 'business') and request.user.business is not None

        return JsonResponse({
            'authenticated': True,
            'user': {
                'id': request.user.id,
                'username': request.user.username,
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'is_staff': request.user.is_staff,
                'is_superuser': request.user.is_superuser,
                'user_type': user_type,
                'has_vendor': has_vendor
            }
        })
    else:
        return JsonResponse({
            'authenticated': False,
            'user': None
        })


def get_csrf_token(request):
    """Get CSRF token for API requests"""
    return JsonResponse({
        'csrf_token': get_token(request)
    })