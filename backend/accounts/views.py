from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator


class CustomLoginView(TemplateView):
    template_name = 'accounts/login.html'
    
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
            return redirect('/dashboard/')
        return super().get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        username = request.POST.get('username')
        password = request.POST.get('password')
        next_url = request.GET.get('next', '/dashboard/')
        
        if username and password:
            # Manual authentication due to Djongo compatibility issues
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            try:
                user = User.objects.get(username=username)
                if user.check_password(password):
                    if user.is_staff or user.is_superuser:
                        # Manual login since authenticate() fails with Djongo
                        from django.contrib.auth import login as auth_login
                        user.backend = 'django.contrib.auth.backends.ModelBackend'
                        auth_login(request, user)
                        messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
                        return redirect(next_url)
                    else:
                        messages.error(request, 'You do not have permission to access the admin panel.')
                else:
                    messages.error(request, 'Invalid username or password.')
            except User.DoesNotExist:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Please provide both username and password.')
        
        return self.get(request, *args, **kwargs)


def custom_logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('/login/')