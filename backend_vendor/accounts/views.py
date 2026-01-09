from django.shortcuts import redirect, render
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth import get_user_model
from django.views import View
from django.conf import settings
import requests
import secrets

User = get_user_model()

# Google OAuth Config
GOOGLE_CLIENT_ID = '735742648650-4fnealrih29hufng0ss2b185iq0o2rf0.apps.googleusercontent.com'
GOOGLE_CLIENT_SECRET = getattr(settings, 'GOOGLE_CLIENT_SECRET', None)  # Add to settings.py


class CustomLoginView(View):
    """Login view that renders the dashboard-style login template"""
    template_name = 'accounts/login.html'

    def get(self, request, *args, **kwargs):
        next_url = request.GET.get('next', '/')

        # If already authenticated, redirect to appropriate dashboard
        if request.user.is_authenticated:
            # Check if user is vendor
            has_vendor = False
            try:
                from vendors.models import Business
                has_vendor = Business.objects.filter(owner=request.user, status='approved').exists()
            except:
                pass

            # Redirect based on role - everyone goes to home, can access dashboards from there
            if has_vendor:
                return redirect('/vendor/')
            elif 'vendor' in next_url:
                return redirect('/vendor/become-vendor/')
            else:
                return redirect('/')

        return render(request, self.template_name, {
            'next_url': next_url
        })

    def post(self, request, *args, **kwargs):
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        next_url = request.POST.get('next', '/')

        if not username or not password:
            return render(request, self.template_name, {
                'error': 'Username/email and password are required',
                'next_url': next_url,
                'username': username
            })

        # Try to find user by username or email
        user = None
        try:
            # First try by username
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                # Try by email
                user = User.objects.get(email=username)

            if user.check_password(password):
                # Manual login since authenticate() can fail with Djongo
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user)

                # Force session save
                request.session.save()

                # Determine redirect URL
                has_vendor = hasattr(user, 'business') and user.business is not None

                if 'vendor' in next_url:
                    if has_vendor:
                        return redirect('/vendor/')
                    else:
                        return redirect('/vendor/become-vendor/')
                elif 'dashboard' in next_url:
                    if user.is_staff or user.is_superuser:
                        return redirect('/dashboard/')
                    else:
                        return redirect('/')
                elif 'account' in next_url:
                    return redirect('/account/')
                else:
                    return redirect(next_url if next_url else '/')
            else:
                return render(request, self.template_name, {
                    'error': 'Invalid username/email or password',
                    'next_url': next_url,
                    'username': username
                })
        except User.DoesNotExist:
            return render(request, self.template_name, {
                'error': 'Invalid username/email or password',
                'next_url': next_url,
                'username': username
            })
        except Exception as e:
            return render(request, self.template_name, {
                'error': 'Login failed. Please try again.',
                'next_url': next_url,
                'username': username
            })


def custom_logout_view(request):
    """Logout and redirect to main site home"""
    logout(request)
    return redirect('home')


class RegisterView(View):
    """Registration view"""
    template_name = 'accounts/register.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('/')

        next_url = request.GET.get('next', '/')
        return render(request, self.template_name, {
            'next_url': next_url
        })

    def post(self, request, *args, **kwargs):
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        next_url = request.POST.get('next', '/')

        # Validation
        errors = []
        if not username:
            errors.append('Username is required')
        if not email:
            errors.append('Email is required')
        if not password:
            errors.append('Password is required')
        if password != password2:
            errors.append('Passwords do not match')
        if len(password) < 6:
            errors.append('Password must be at least 6 characters')

        # Check if username exists
        if User.objects.filter(username=username).exists():
            errors.append('Username already exists')

        # Check if email exists
        if User.objects.filter(email=email).exists():
            errors.append('Email already registered')

        if errors:
            return render(request, self.template_name, {
                'errors': errors,
                'next_url': next_url,
                'username': username,
                'email': email,
                'first_name': first_name,
                'last_name': last_name
            })

        try:
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )

            # Auto login
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            request.session.save()

            return redirect(next_url if next_url else '/')

        except Exception as e:
            return render(request, self.template_name, {
                'errors': ['Registration failed. Please try again.'],
                'next_url': next_url,
                'username': username,
                'email': email,
                'first_name': first_name,
                'last_name': last_name
            })


def google_oauth_redirect(request):
    """Redirect user to Google OAuth authorization page (server-side flow)"""
    # Save the next URL in session
    next_url = request.GET.get('next', '/')
    request.session['oauth_next_url'] = next_url

    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    request.session['oauth_state'] = state

    # Build the redirect URI
    redirect_uri = request.build_absolute_uri('/accounts/google/callback/')

    # Build Google OAuth URL
    auth_url = (
        'https://accounts.google.com/o/oauth2/v2/auth?'
        f'client_id={GOOGLE_CLIENT_ID}&'
        f'redirect_uri={redirect_uri}&'
        'response_type=code&'
        'scope=openid%20email%20profile&'
        f'state={state}&'
        'access_type=offline&'
        'prompt=select_account'
    )

    return redirect(auth_url)


def google_oauth_callback(request):
    """Handle Google OAuth callback (server-side flow)"""
    from django.contrib import messages

    # Verify state
    state = request.GET.get('state')
    saved_state = request.session.get('oauth_state')

    if not state or state != saved_state:
        messages.error(request, 'Invalid OAuth state. Please try again.')
        return redirect('/login/')

    # Get authorization code
    code = request.GET.get('code')
    error = request.GET.get('error')

    if error:
        messages.error(request, f'Google sign-in was cancelled or failed: {error}')
        return redirect('/login/')

    if not code:
        messages.error(request, 'No authorization code received from Google.')
        return redirect('/login/')

    # Exchange code for tokens
    redirect_uri = request.build_absolute_uri('/accounts/google/callback/')

    try:
        token_response = requests.post(
            'https://oauth2.googleapis.com/token',
            data={
                'code': code,
                'client_id': GOOGLE_CLIENT_ID,
                'client_secret': GOOGLE_CLIENT_SECRET,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code'
            }
        )

        if token_response.status_code != 200:
            print(f"Token exchange failed: {token_response.text}")
            messages.error(request, 'Failed to authenticate with Google. Please try again.')
            return redirect('/login/')

        tokens = token_response.json()
        access_token = tokens.get('access_token')

        # Get user info
        userinfo_response = requests.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': f'Bearer {access_token}'}
        )

        if userinfo_response.status_code != 200:
            messages.error(request, 'Failed to get user info from Google.')
            return redirect('/login/')

        userinfo = userinfo_response.json()
        email = userinfo.get('email')
        given_name = userinfo.get('given_name', '')
        family_name = userinfo.get('family_name', '')
        picture = userinfo.get('picture', '')

        if not email:
            messages.error(request, 'No email received from Google.')
            return redirect('/login/')

        # Find or create user
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Create new user
            username = email.split('@')[0]
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=given_name,
                last_name=family_name,
                password=None
            )
            user.is_verified = True
            user.save()

        # Log user in
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)
        request.session.save()

        # Determine redirect URL
        next_url = request.session.pop('oauth_next_url', '/')
        request.session.pop('oauth_state', None)

        # Check if user is vendor
        has_vendor = False
        try:
            from vendors.models import Business
            has_vendor = Business.objects.filter(owner=user, status='approved').exists()
        except:
            pass

        # Redirect based on context - go to home, users can access dashboards from navbar
        if 'vendor' in next_url:
            if has_vendor:
                return redirect('/vendor/')
            else:
                return redirect('/vendor/become-vendor/')
        elif next_url and next_url != '/':
            return redirect(next_url)
        elif has_vendor:
            return redirect('/vendor/')
        else:
            return redirect('/')

    except Exception as e:
        print(f"Google OAuth error: {e}")
        import traceback
        traceback.print_exc()
        messages.error(request, 'Authentication failed. Please try again.')
        return redirect('/login/')
