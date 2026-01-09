"""
Google OAuth Authentication Handler
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model, login
import json
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import requests

User = get_user_model()

# Google OAuth Client ID (should match frontend)
GOOGLE_CLIENT_ID = '735742648650-4fnealrih29hufng0ss2b185iq0o2rf0.apps.googleusercontent.com'


@csrf_exempt
@require_POST
def google_auth(request):
    """
    Authenticate user with Google OAuth token (ID token or Access token)
    Creates user if doesn't exist, logs them in
    """
    try:
        data = json.loads(request.body)
        token = data.get('idToken')
        access_token = data.get('accessToken')
        
        if not token and not access_token:
            return JsonResponse({
                'success': False,
                'error': 'No token provided'
            }, status=400)
        
        # Try to get user info - try ID token first, then access token
        email = None
        given_name = ''
        family_name = ''
        picture = ''
        google_id = None
        
        try:
            # Try ID token verification
            idinfo = id_token.verify_oauth2_token(
                token, 
                google_requests.Request(), 
                GOOGLE_CLIENT_ID
            )
            
            email = idinfo.get('email')
            given_name = idinfo.get('given_name', '')
            family_name = idinfo.get('family_name', '')
            picture = idinfo.get('picture', '')
            google_id = idinfo.get('sub')
            
            print(f"SUCCESS: ID token verified for: {email}")
            
        except Exception as e:
            # If ID token fails, try access token
            print(f"WARNING: ID token verification failed, trying access token: {e}")
            
            try:
                # Use access token to get user info from Google API
                user_info_url = f'https://www.googleapis.com/oauth2/v2/userinfo?access_token={access_token or token}'
                response = requests.get(user_info_url)
                
                if response.status_code == 200:
                    user_data = response.json()
                    email = user_data.get('email')
                    given_name = user_data.get('given_name', '')
                    family_name = user_data.get('family_name', '')
                    picture = user_data.get('picture', '')
                    google_id = user_data.get('id')
                    
                    print(f"SUCCESS: Access token verified for: {email}")
                else:
                    return JsonResponse({
                        'success': False,
                        'error': 'Failed to verify Google token'
                    }, status=401)
                    
            except Exception as access_error:
                print(f"ERROR: Access token verification failed: {access_error}")
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid Google token'
                }, status=401)
        
        if not email:
            return JsonResponse({
                'success': False,
                'error': 'No email found in token'
            }, status=400)
        
        # Try to get existing user by email
        is_new_user = False
        try:
            user = User.objects.get(email=email)
            print(f"SUCCESS: Existing user found: {email}")
        except User.DoesNotExist:
            # Create new user
            is_new_user = True
            username = email.split('@')[0]

            # Make username unique if it exists
            base_username = username
            counter = 1
            while True:
                try:
                    User.objects.get(username=username)
                    username = f"{base_username}{counter}"
                    counter += 1
                except User.DoesNotExist:
                    break

            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=given_name,
                last_name=family_name,
                password=None  # No password for OAuth users
            )
            user.is_verified = True
            user.save()
            print(f"SUCCESS: New user created: {email}")

        # Log the user in
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)

        # Force session save and set session cookie
        request.session.modified = True
        request.session.save()

        # Check if user is a vendor (import here to avoid circular imports)
        is_vendor = False
        vendor_business = None
        try:
            from vendors.models import Business
            # Check if user is already linked to a business
            vendor_business = Business.objects.filter(owner=user, status='approved').first()
            if vendor_business:
                is_vendor = True
            else:
                # Check if there's an unlinked business with this email
                unlinked_business = Business.objects.filter(
                    email__iexact=user.email,
                    owner__isnull=True,
                    status='approved'
                ).first()
                if unlinked_business:
                    unlinked_business.owner = user
                    unlinked_business.save()
                    vendor_business = unlinked_business
                    is_vendor = True
                    request.session['new_vendor'] = True
                    print(f"SUCCESS: User {email} linked to business {unlinked_business.business_name}")
        except Exception as vendor_error:
            print(f"WARNING: Vendor check failed (vendors app may not be installed): {vendor_error}")

        # Determine redirect URL based on user role
        if is_vendor:
            redirect_url = '/vendor/'
            user_type = 'vendor'
        elif user.is_staff or user.is_superuser:
            redirect_url = '/dashboard/'
            user_type = 'admin'
        else:
            redirect_url = '/'
            user_type = 'customer'

        # Different message for new vs returning users
        display_name = user.get_full_name() or user.username
        if is_new_user:
            if is_vendor:
                message = f'Welcome to your vendor dashboard, {display_name}!'
            else:
                message = f'Welcome to OVN Store, {display_name}! Your account has been created.'
        else:
            if is_vendor:
                message = f'Welcome back, {display_name}! Redirecting to your vendor dashboard.'
            else:
                message = f'Welcome back, {display_name}!'

        return JsonResponse({
            'success': True,
            'message': message,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'picture': picture,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'is_vendor': is_vendor,
                'vendor_business': vendor_business.business_name if vendor_business else None,
                'user_type': user_type
            },
            'redirect_url': redirect_url
        })
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        print(f"ERROR: Google auth error: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': 'Authentication failed. Please try again.'
        }, status=500)
