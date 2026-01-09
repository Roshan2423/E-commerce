"""
Email notifications for vendor subscription system
"""
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone


def get_from_email():
    """Get the from email address"""
    return getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@ovnstore.com')


def send_vendor_approval_email(application, business):
    """
    Send email to vendor when their application is approved
    """
    subject = f"Congratulations! Your {business.business_name} vendor application has been approved!"

    context = {
        'business': business,
        'application': application,
        'trial_days': 14,
        'plan_name': business.get_plan_display(),
        'dashboard_url': '/vendor/',
    }

    # Render templates
    text_content = render_to_string('emails/vendor_approved.txt', context)
    html_content = render_to_string('emails/vendor_approved.html', context)

    # Create email
    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=get_from_email(),
        to=[application.business_email],
    )
    msg.attach_alternative(html_content, "text/html")

    try:
        msg.send()
        return True
    except Exception as e:
        print(f"Failed to send approval email: {e}")
        return False


def send_trial_expiry_reminder(business):
    """
    Send reminder email 3 days before trial expires
    """
    subject = f"Your {business.business_name} trial expires in {business.trial_days_remaining} days!"

    context = {
        'business': business,
        'days_remaining': business.trial_days_remaining,
        'plan_name': business.get_plan_display(),
        'upgrade_url': '/vendor/upgrade/',
        'trial_end_date': business.trial_end_date,
    }

    # Render templates
    text_content = render_to_string('emails/trial_expiry_reminder.txt', context)
    html_content = render_to_string('emails/trial_expiry_reminder.html', context)

    # Get vendor email
    to_email = business.owner.email if business.owner else None
    if not to_email:
        print(f"No email found for business: {business.business_name}")
        return False

    # Create email
    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=get_from_email(),
        to=[to_email],
    )
    msg.attach_alternative(html_content, "text/html")

    try:
        msg.send()
        return True
    except Exception as e:
        print(f"Failed to send trial expiry reminder: {e}")
        return False


def send_trial_expired_email(business):
    """
    Send email when trial has expired
    """
    subject = f"Your {business.business_name} free trial has expired"

    context = {
        'business': business,
        'plan_name': business.get_plan_display(),
        'upgrade_url': '/vendor/upgrade/',
    }

    # Render templates
    text_content = render_to_string('emails/trial_expired.txt', context)
    html_content = render_to_string('emails/trial_expired.html', context)

    # Get vendor email
    to_email = business.owner.email if business.owner else None
    if not to_email:
        print(f"No email found for business: {business.business_name}")
        return False

    # Create email
    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=get_from_email(),
        to=[to_email],
    )
    msg.attach_alternative(html_content, "text/html")

    try:
        msg.send()
        # Mark that expiry email was sent
        business.trial_expiry_email_sent = True
        business.save(update_fields=['trial_expiry_email_sent'])
        return True
    except Exception as e:
        print(f"Failed to send trial expired email: {e}")
        return False
