"""
Vendor Application Views
Allow users to apply to become vendors
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, TemplateView, DetailView, ListView
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import HttpResponseRedirect

from .models import VendorApplication, Business


class VendorApplicationCreateView(LoginRequiredMixin, CreateView):
    """Submit a new vendor application"""
    model = VendorApplication
    template_name = 'vendor/apply/form.html'
    fields = ['date_of_birth', 'business_name', 'business_email', 'phone', 'description', 'category', 'address', 'business_document', 'selected_plan']
    success_url = reverse_lazy('vendor:application_success')

    def dispatch(self, request, *args, **kwargs):
        # Check if user already has an approved business
        if hasattr(request.user, 'business') and request.user.business:
            messages.info(request, 'You already have a vendor account.')
            return redirect('vendor:dashboard')

        # Check if user has a pending application
        pending = VendorApplication.objects.filter(
            user=request.user,
            status__in=['pending', 'more_info']
        ).first()
        if pending:
            return redirect('vendor:application_status', pk=pending.pk)

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.user = self.request.user
        # Pre-fill email if not provided
        if not form.instance.business_email:
            form.instance.business_email = self.request.user.email
        messages.success(self.request, 'Your vendor application has been submitted successfully!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category_choices'] = VendorApplication.CATEGORY_CHOICES
        context['plan_choices'] = VendorApplication.PLAN_CHOICES
        return context


class VendorApplicationSuccessView(LoginRequiredMixin, TemplateView):
    """Application submitted successfully"""
    template_name = 'vendor/apply/success.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['application'] = VendorApplication.objects.filter(
            user=self.request.user
        ).order_by('-submitted_at').first()
        return context


class VendorApplicationStatusView(LoginRequiredMixin, DetailView):
    """Check application status"""
    model = VendorApplication
    template_name = 'vendor/apply/status.html'
    context_object_name = 'application'

    def get_queryset(self):
        return VendorApplication.objects.filter(user=self.request.user)


class MyApplicationsView(LoginRequiredMixin, ListView):
    """List all applications by the current user"""
    model = VendorApplication
    template_name = 'vendor/apply/my_applications.html'
    context_object_name = 'applications'

    def get_queryset(self):
        return VendorApplication.objects.filter(user=self.request.user)


# Landing page for "Become a Vendor"
class BecomeVendorView(TemplateView):
    """Landing page explaining vendor benefits"""
    template_name = 'vendor/apply/landing.html'

    def dispatch(self, request, *args, **kwargs):
        # If user is already a vendor, redirect to dashboard
        if request.user.is_authenticated:
            if hasattr(request.user, 'business') and request.user.business:
                return redirect('vendor:dashboard')
        return super().dispatch(request, *args, **kwargs)
