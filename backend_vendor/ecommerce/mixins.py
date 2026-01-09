from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from urllib.parse import quote


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to require admin/staff access for views"""

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def handle_no_permission(self):
        """Redirect to frontend login if not authenticated or not staff"""
        if not self.request.user.is_authenticated:
            # Redirect to login with return URL (same server)
            next_url = quote(self.request.path, safe='')
            return redirect(f'/login?next={next_url}')
        else:
            # User is authenticated but not staff - redirect to home
            return redirect('/')
