from .models import Review


def pending_reviews_count(request):
    """Context processor to provide pending reviews count to all templates"""
    count = 0
    if request.user.is_authenticated and request.user.is_staff:
        try:
            count = Review.objects.filter(status='pending').count()
        except Exception:
            count = 0
    return {
        'pending_reviews_count': count
    }
