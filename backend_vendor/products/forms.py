from django import forms
from .models import Product, Category, ProductImage, ProductVariant


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'short_description', 'category', 
            'price', 'compare_price', 'cost_price', 'sku', 
            'stock_quantity', 'low_stock_threshold', 'weight', 
            'length', 'width', 'height', 'is_active', 'is_featured',
            'meta_title', 'meta_description'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'short_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'compare_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'cost_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'sku': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Leave blank to auto-generate'
            }),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'low_stock_threshold': forms.NumberInput(attrs={'class': 'form-control'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'length': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'width': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'height': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'meta_title': forms.TextInput(attrs={'class': 'form-control'}),
            'meta_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make SKU field not required since it will be auto-generated
        self.fields['sku'].required = False
        # Make low_stock_threshold optional with default value
        self.fields['low_stock_threshold'].required = False
        self.fields['low_stock_threshold'].initial = 10

    def clean_weight(self):
        weight = self.cleaned_data.get('weight')
        if weight is not None:
            # Convert to string to check decimal places
            weight_str = str(weight)
            if '.' in weight_str:
                decimal_places = len(weight_str.split('.')[1])
                if decimal_places > 2:
                    raise forms.ValidationError("Ensure that there are no more than 2 decimal places.")
        return weight

    def clean_length(self):
        length = self.cleaned_data.get('length')
        if length is not None:
            length_str = str(length)
            if '.' in length_str:
                decimal_places = len(length_str.split('.')[1])
                if decimal_places > 2:
                    raise forms.ValidationError("Ensure that there are no more than 2 decimal places.")
        return length

    def clean_width(self):
        width = self.cleaned_data.get('width')
        if width is not None:
            width_str = str(width)
            if '.' in width_str:
                decimal_places = len(width_str.split('.')[1])
                if decimal_places > 2:
                    raise forms.ValidationError("Ensure that there are no more than 2 decimal places.")
        return width

    def clean_height(self):
        height = self.cleaned_data.get('height')
        if height is not None:
            height_str = str(height)
            if '.' in height_str:
                decimal_places = len(height_str.split('.')[1])
                if decimal_places > 2:
                    raise forms.ValidationError("Ensure that there are no more than 2 decimal places.")
        return height


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image', 'alt_text', 'is_main']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'alt_text': forms.TextInput(attrs={'class': 'form-control'}),
            'is_main': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ['name', 'value', 'price_adjustment', 'stock_quantity', 'sku', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'value': forms.TextInput(attrs={'class': 'form-control'}),
            'price_adjustment': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'sku': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }