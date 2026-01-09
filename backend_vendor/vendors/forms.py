"""
Vendor Forms
"""
from django import forms
from .models import Business, VendorStorefront


class BusinessForm(forms.ModelForm):
    """Form for super admin to add new business"""
    class Meta:
        model = Business
        fields = ['email', 'business_name', 'description', 'phone', 'address', 'status', 'commission_rate']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'business@email.com'
            }),
            'business_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Business Name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Brief description of the business'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+977-XXXXXXXXXX'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Business address'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'commission_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
        }


class StorefrontForm(forms.ModelForm):
    """Form for vendor to customize their storefront"""
    class Meta:
        model = VendorStorefront
        exclude = ['business', 'created_at', 'updated_at']
        widgets = {
            'hero_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Welcome to Our Store'
            }),
            'hero_subtitle': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Discover amazing products'
            }),
            'hero_cta_text': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Shop Now'
            }),
            'hero_cta_link': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '/products'
            }),
            'primary_color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            }),
            'secondary_color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            }),
            'accent_color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            }),
            'product_layout': forms.Select(attrs={'class': 'form-select'}),
            'products_per_page': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '4',
                'max': '48'
            }),
            'facebook_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://facebook.com/yourpage'
            }),
            'instagram_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://instagram.com/yourhandle'
            }),
            'twitter_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://twitter.com/yourhandle'
            }),
            'tiktok_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://tiktok.com/@yourhandle'
            }),
            'youtube_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://youtube.com/yourchannel'
            }),
            'meta_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'SEO Title'
            }),
            'meta_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'SEO Description'
            }),
            'google_analytics_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'UA-XXXXXXXX-X or G-XXXXXXXXXX'
            }),
            'facebook_pixel_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'XXXXXXXXXXXXXXXX'
            }),
        }


class ProfessionalStorefrontForm(forms.ModelForm):
    """Extended form for professional plan vendors with advanced customization"""

    class Meta:
        model = VendorStorefront
        exclude = ['business', 'created_at', 'updated_at']
        widgets = {
            # Basic Hero Section
            'hero_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Welcome to Our Store'
            }),
            'hero_subtitle': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Discover amazing products'
            }),
            'hero_cta_text': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Shop Now'
            }),
            'hero_cta_link': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '/products'
            }),

            # Brand Colors
            'primary_color': forms.TextInput(attrs={
                'class': 'form-control color-picker',
                'type': 'color'
            }),
            'secondary_color': forms.TextInput(attrs={
                'class': 'form-control color-picker',
                'type': 'color'
            }),
            'accent_color': forms.TextInput(attrs={
                'class': 'form-control color-picker',
                'type': 'color'
            }),

            # Layout
            'product_layout': forms.Select(attrs={'class': 'form-select'}),
            'products_per_page': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '4',
                'max': '48'
            }),

            # Professional: Header Style
            'header_style': forms.Select(attrs={'class': 'form-select header-style-select'}),

            # Professional: Hero Style
            'hero_style': forms.Select(attrs={'class': 'form-select hero-style-select'}),

            # Professional: Additional Hero Slides
            'hero_title_2': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Slide 2 Title'
            }),
            'hero_subtitle_2': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Slide 2 Subtitle'
            }),
            'hero_cta_text_2': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Shop Now'
            }),
            'hero_cta_link_2': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '/products'
            }),
            'hero_title_3': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Slide 3 Title'
            }),
            'hero_subtitle_3': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Slide 3 Subtitle'
            }),
            'hero_cta_text_3': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Shop Now'
            }),
            'hero_cta_link_3': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '/products'
            }),

            # Professional: Hero Overlay
            'hero_overlay_color': forms.TextInput(attrs={
                'class': 'form-control color-picker',
                'type': 'color'
            }),
            'hero_overlay_opacity': forms.NumberInput(attrs={
                'class': 'form-control opacity-slider',
                'type': 'range',
                'min': '0',
                'max': '100',
                'step': '5'
            }),

            # Professional: Storefront Template
            'storefront_template': forms.Select(attrs={'class': 'form-select template-select'}),

            # Professional: Dashboard Theme
            'dashboard_primary_color': forms.TextInput(attrs={
                'class': 'form-control color-picker',
                'type': 'color'
            }),
            'dashboard_sidebar_color': forms.TextInput(attrs={
                'class': 'form-control color-picker',
                'type': 'color'
            }),
            'dashboard_accent_color': forms.TextInput(attrs={
                'class': 'form-control color-picker',
                'type': 'color'
            }),

            # Social Links
            'facebook_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://facebook.com/yourpage'
            }),
            'instagram_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://instagram.com/yourhandle'
            }),
            'twitter_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://twitter.com/yourhandle'
            }),
            'tiktok_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://tiktok.com/@yourhandle'
            }),
            'youtube_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://youtube.com/yourchannel'
            }),

            # SEO
            'meta_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'SEO Title'
            }),
            'meta_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'SEO Description'
            }),
            'google_analytics_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'UA-XXXXXXXX-X or G-XXXXXXXXXX'
            }),
            'facebook_pixel_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'XXXXXXXXXXXXXXXX'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.is_professional = kwargs.pop('is_professional', True)
        super().__init__(*args, **kwargs)

        # If not professional plan, remove pro-only fields
        if not self.is_professional:
            pro_only_fields = [
                'header_style', 'hero_style',
                'hero_image_2', 'hero_image_3',
                'hero_title_2', 'hero_subtitle_2', 'hero_cta_text_2', 'hero_cta_link_2',
                'hero_title_3', 'hero_subtitle_3', 'hero_cta_text_3', 'hero_cta_link_3',
                'hero_overlay_color', 'hero_overlay_opacity',
                'storefront_template',
                'dashboard_primary_color', 'dashboard_sidebar_color', 'dashboard_accent_color',
                'layout_template', 'section_order', 'sections_enabled',
                'show_hero', 'show_featured', 'show_new_arrivals', 'show_testimonials', 'show_newsletter'
            ]
            for field in pro_only_fields:
                if field in self.fields:
                    del self.fields[field]


class VendorMessageForm(forms.Form):
    """Form for sending messages"""
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Subject'
        })
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Your message...'
        })
    )


class VendorReplyForm(forms.Form):
    """Form for replying to messages"""
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Type your reply...'
        })
    )
