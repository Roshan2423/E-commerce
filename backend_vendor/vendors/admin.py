"""
Django Admin configuration for Vendors app
(Optional - for Django's built-in admin if needed)
"""
from django.contrib import admin
from .models import Business, VendorStorefront, VendorMessage, VendorPayout, VendorApplication


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ['business_name', 'email', 'status', 'owner', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['business_name', 'email', 'owner__email']
    readonly_fields = ['created_at', 'updated_at', 'approved_at']
    prepopulated_fields = {'slug': ('business_name',)}


@admin.register(VendorStorefront)
class VendorStorefrontAdmin(admin.ModelAdmin):
    list_display = ['business', 'primary_color', 'product_layout', 'updated_at']
    search_fields = ['business__business_name']


@admin.register(VendorMessage)
class VendorMessageAdmin(admin.ModelAdmin):
    list_display = ['subject', 'business', 'customer', 'is_read', 'is_from_vendor', 'created_at']
    list_filter = ['is_read', 'is_from_vendor', 'created_at']
    search_fields = ['subject', 'message', 'business__business_name']


@admin.register(VendorPayout)
class VendorPayoutAdmin(admin.ModelAdmin):
    list_display = ['business', 'amount', 'net_amount', 'status', 'period_start', 'period_end']
    list_filter = ['status', 'created_at']
    search_fields = ['business__business_name', 'transaction_id']


@admin.register(VendorApplication)
class VendorApplicationAdmin(admin.ModelAdmin):
    list_display = ['business_name', 'user', 'business_email', 'category', 'status', 'submitted_at']
    list_filter = ['status', 'category', 'submitted_at']
    search_fields = ['business_name', 'business_email', 'user__email', 'user__username']
    readonly_fields = ['submitted_at', 'updated_at', 'reviewed_at']
    list_editable = ['status']
    ordering = ['-submitted_at']

    fieldsets = (
        ('Applicant Info', {
            'fields': ('user',)
        }),
        ('Business Details', {
            'fields': ('business_name', 'business_email', 'phone', 'category', 'description', 'address', 'business_document')
        }),
        ('Review Status', {
            'fields': ('status', 'admin_notes', 'rejection_reason', 'reviewed_by', 'reviewed_at')
        }),
        ('Result', {
            'fields': ('created_business',)
        }),
        ('Timestamps', {
            'fields': ('submitted_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
