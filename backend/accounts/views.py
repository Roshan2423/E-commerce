from django.shortcuts import redirect
from django.contrib.auth import logout
from django.views import View


class CustomLoginView(View):
    """Redirect to frontend login page (same server)"""

    def get(self, request, *args, **kwargs):
        # If already authenticated and is admin, go to dashboard
        if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
            return redirect('/dashboard/')

        # Redirect to frontend login (same server)
        next_url = request.GET.get('next', '/dashboard/')
        return redirect(f'/login?next={next_url}')

    def post(self, request, *args, **kwargs):
        # Redirect POST requests to frontend login
        return redirect('/login')


def custom_logout_view(request):
    """Logout and redirect to home"""
    logout(request)
    return redirect('/')