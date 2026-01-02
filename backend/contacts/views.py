from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.contrib import messages
import json
from .models import ContactMessage


@csrf_exempt
@require_http_methods(["POST"])
def submit_contact(request):
    """API endpoint to receive contact form submissions"""
    try:
        data = json.loads(request.body)

        # Validate required fields
        required_fields = ['name', 'email', 'subject', 'message']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({
                    'success': False,
                    'error': f'{field.title()} is required'
                }, status=400)

        # Create contact message
        contact = ContactMessage.objects.create(
            name=data.get('name'),
            email=data.get('email'),
            phone=data.get('phone', ''),
            subject=data.get('subject'),
            message=data.get('message')
        )

        return JsonResponse({
            'success': True,
            'message': 'Thank you for your message! We will get back to you soon.',
            'id': str(contact.id)
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@staff_member_required
def contact_list(request):
    """Admin view to list all contact messages"""
    status_filter = request.GET.get('status', '')
    subject_filter = request.GET.get('subject', '')

    contacts = ContactMessage.objects.all()

    if status_filter:
        contacts = contacts.filter(status=status_filter)
    if subject_filter:
        contacts = contacts.filter(subject=subject_filter)

    # Count by status
    new_count = ContactMessage.objects.filter(status='new').count()
    read_count = ContactMessage.objects.filter(status='read').count()
    replied_count = ContactMessage.objects.filter(status='replied').count()
    resolved_count = ContactMessage.objects.filter(status='resolved').count()

    paginator = Paginator(contacts, 20)
    page = request.GET.get('page', 1)
    contacts = paginator.get_page(page)

    context = {
        'contacts': contacts,
        'status_filter': status_filter,
        'subject_filter': subject_filter,
        'new_count': new_count,
        'read_count': read_count,
        'replied_count': replied_count,
        'resolved_count': resolved_count,
        'status_choices': ContactMessage.STATUS_CHOICES,
        'subject_choices': ContactMessage.SUBJECT_CHOICES,
    }
    return render(request, 'admin/contacts/list.html', context)


@staff_member_required
def contact_detail(request, pk):
    """Admin view to see contact message details"""
    contact = get_object_or_404(ContactMessage, pk=pk)
    auto_marked_read = False

    if request.method == 'POST':
        status = request.POST.get('status')
        admin_notes = request.POST.get('admin_notes')

        if status:
            contact.status = status
        if admin_notes is not None:
            contact.admin_notes = admin_notes

        contact.save()
        messages.success(request, 'Contact message updated successfully.')

        # Redirect to list page to avoid auto-read triggering again
        return redirect('contacts:contact_list')
    else:
        # Only auto-mark as read on first view (GET request)
        if contact.status == 'new':
            contact.status = 'read'
            contact.save()
            auto_marked_read = True

    context = {
        'contact': contact,
        'status_choices': ContactMessage.STATUS_CHOICES,
        'auto_marked_read': auto_marked_read,
    }
    return render(request, 'admin/contacts/detail.html', context)


@staff_member_required
@require_http_methods(["POST"])
def contact_delete(request, pk):
    """Delete a contact message"""
    contact = get_object_or_404(ContactMessage, pk=pk)
    contact.delete()
    messages.success(request, 'Contact message deleted successfully.')
    return redirect('contacts:contact_list')
