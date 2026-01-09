from .models import ContactMessage


def unread_messages_count(request):
    """Context processor to provide unread messages count to all templates"""
    count = 0
    if request.user.is_authenticated and request.user.is_staff:
        count = ContactMessage.objects.filter(status='new').count()
    return {
        'unread_messages_count': count
    }
