from django import forms
from .models import Order, ShippingMethod


class OrderUpdateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'status', 'payment_status', 'shipping_method', 
            'tracking_number', 'notes'
        ]
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'payment_status': forms.Select(attrs={'class': 'form-control'}),
            'shipping_method': forms.TextInput(attrs={'class': 'form-control'}),
            'tracking_number': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add helpful text to fields
        self.fields['status'].help_text = "Update the order status to track its progress"
        self.fields['payment_status'].help_text = "Update payment status based on payment confirmation"
        self.fields['tracking_number'].help_text = "Enter tracking number when order is shipped"
        self.fields['notes'].help_text = "Add any internal notes about this order"