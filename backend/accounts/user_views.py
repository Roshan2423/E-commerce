from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from .models import User, Address
from ecommerce.mixins import AdminRequiredMixin


class UserListView(AdminRequiredMixin, ListView):
    """List view for all users with filtering and search"""
    model = User
    template_name = 'admin/users/list.html'
    context_object_name = 'users'
    paginate_by = 25

    def get_queryset(self):
        try:
            # Get all users first
            all_users = list(User.objects.all())

            # Get filter parameters
            search = self.request.GET.get('search', '').strip().lower()
            role = self.request.GET.get('role', '')
            status = self.request.GET.get('status', '')

            # Filter by search term (name or email)
            if search:
                all_users = [
                    user for user in all_users
                    if search in user.email.lower()
                    or search in user.username.lower()
                    or search in (user.first_name or '').lower()
                    or search in (user.last_name or '').lower()
                    or search in (user.get_full_name() or '').lower()
                ]

            # Filter by role
            if role == 'admin':
                all_users = [user for user in all_users if user.is_staff or user.is_superuser]
            elif role == 'customer':
                all_users = [user for user in all_users if not user.is_staff and not user.is_superuser]

            # Filter by status
            if status == 'active':
                all_users = [user for user in all_users if user.is_active]
            elif status == 'inactive':
                all_users = [user for user in all_users if not user.is_active]

            return all_users

        except Exception as e:
            return []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add filter parameters to context for maintaining state
        context['current_search'] = self.request.GET.get('search', '')
        context['current_role'] = self.request.GET.get('role', '')
        context['current_status'] = self.request.GET.get('status', '')

        # Calculate stats from all users (not filtered)
        try:
            all_users = list(User.objects.all())
            context['total_users'] = len(all_users)
            context['staff_users'] = sum(1 for user in all_users if user.is_staff or user.is_superuser)
            context['active_users'] = sum(1 for user in all_users if user.is_active)

        except Exception as e:
            context['total_users'] = 0
            context['staff_users'] = 0
            context['active_users'] = 0

        return context


class UserDetailView(AdminRequiredMixin, DetailView):
    """Detail view for individual user"""
    model = User
    template_name = 'admin/users/detail.html'
    context_object_name = 'user_detail'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        
        # Get user's addresses with error handling
        try:
            context['user_addresses'] = list(user.addresses.all())
        except:
            context['user_addresses'] = []
        
        # Get user's orders with better error handling
        try:
            from orders.models import Order
            user_orders = Order.objects.filter(user=user)
            context['user_orders'] = list(user_orders)[:10]  # Convert to list and limit
            context['total_orders'] = len(list(user_orders))  # Manual count
        except Exception as e:
            context['user_orders'] = []
            context['total_orders'] = 0
        
        return context


@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def toggle_user_status(request, user_id):
    """Toggle user active status via AJAX"""
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)

        # Prevent deactivating superusers
        if user.is_superuser and user.is_active:
            return JsonResponse({
                'success': False,
                'message': 'Cannot deactivate superuser accounts'
            })

        user.is_active = not user.is_active
        user.save()

        return JsonResponse({
            'success': True,
            'new_status': user.is_active,
            'message': f'User {"activated" if user.is_active else "deactivated"} successfully'
        })

    return JsonResponse({'success': False, 'message': 'Invalid request'})


@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def toggle_user_verification(request, user_id):
    """Toggle user verification status via AJAX"""
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        user.is_verified = not user.is_verified
        user.save()
        
        return JsonResponse({
            'success': True,
            'new_status': user.is_verified,
            'message': f'User {"verified" if user.is_verified else "unverified"} successfully'
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})


@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def bulk_user_actions(request):
    """Handle bulk actions on users"""
    if request.method == 'POST':
        action = request.POST.get('action')
        user_ids = request.POST.getlist('user_ids')

        if not user_ids:
            messages.error(request, 'No users selected.')
            return redirect('user_management:user_list')

        users = User.objects.filter(id__in=user_ids)

        if action == 'activate':
            users.update(is_active=True)
            messages.success(request, f'{users.count()} users activated successfully.')
        elif action == 'deactivate':
            users.update(is_active=False)
            messages.success(request, f'{users.count()} users deactivated successfully.')
        elif action == 'verify':
            users.update(is_verified=True)
            messages.success(request, f'{users.count()} users verified successfully.')
        elif action == 'unverify':
            users.update(is_verified=False)
            messages.success(request, f'{users.count()} users unverified successfully.')
        else:
            messages.error(request, 'Invalid action selected.')

    return redirect('user_management:user_list')


@login_required
@user_passes_test(lambda u: u.is_superuser)
def toggle_admin_status(request, user_id):
    """Toggle user admin (staff) status - only superusers can do this"""
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)

        # Prevent toggling superuser status
        if user.is_superuser:
            return JsonResponse({
                'success': False,
                'message': 'Cannot change superuser status'
            })

        user.is_staff = not user.is_staff
        user.save()

        return JsonResponse({
            'success': True,
            'is_admin': user.is_staff,
            'message': f'User {"promoted to admin" if user.is_staff else "demoted to customer"} successfully'
        })

    return JsonResponse({'success': False, 'message': 'Invalid request'})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def delete_user(request, user_id):
    """Delete a user - only superusers can do this"""
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)

        # Prevent deleting superusers
        if user.is_superuser:
            return JsonResponse({
                'success': False,
                'message': 'Cannot delete superuser accounts'
            })

        # Prevent deleting yourself
        if user.id == request.user.id:
            return JsonResponse({
                'success': False,
                'message': 'Cannot delete your own account'
            })

        user_name = user.get_full_name() or user.email
        user.delete()

        return JsonResponse({
            'success': True,
            'message': f'User "{user_name}" deleted successfully'
        })

    return JsonResponse({'success': False, 'message': 'Invalid request'})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def edit_user(request, pk):
    """Edit user details - cannot edit name, username, or full name"""
    user = get_object_or_404(User, id=pk)

    if request.method == 'POST':
        # Validate phone number (must be exactly 10 digits if provided)
        phone_number = request.POST.get('phone_number', '').strip()
        if phone_number:
            # Remove any non-digit characters
            phone_number = ''.join(filter(str.isdigit, phone_number))
            if len(phone_number) != 10:
                messages.error(request, 'Phone number must be exactly 10 digits')
                return render(request, 'admin/users/edit.html', {'user_obj': user})

        # Only allow editing specific fields
        user.email = request.POST.get('email', user.email)
        user.phone_number = phone_number if phone_number else None
        user.is_active = request.POST.get('is_active') == 'on'
        user.is_verified = request.POST.get('is_verified') == 'on'

        # Prevent deactivating superusers
        if user.is_superuser:
            user.is_active = True

        # Only superusers can change staff status, and cannot change superuser status
        if request.user.is_superuser and not user.is_superuser:
            user.is_staff = request.POST.get('is_staff') == 'on'

        user.save()
        messages.success(request, f'User "{user.get_full_name() or user.email}" updated successfully')
        return redirect('user_management:user_list')

    return render(request, 'admin/users/edit.html', {'user_obj': user})