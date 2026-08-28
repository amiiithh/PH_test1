from django import forms
from .models import Address


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['full_name', 'phone', 'line1', 'line2', 'city', 'state', 'pincode']
        widgets = {
            'full_name': forms.TextInput(attrs={'placeholder': 'Full name'}),
            'phone': forms.TextInput(attrs={'placeholder': '10-digit mobile number'}),
            'line1': forms.TextInput(attrs={'placeholder': 'House no., building, street'}),
            'line2': forms.TextInput(attrs={'placeholder': 'Area, landmark (optional)'}),
            'city': forms.TextInput(attrs={'placeholder': 'City'}),
            'state': forms.TextInput(attrs={'placeholder': 'State'}),
            'pincode': forms.TextInput(attrs={'placeholder': 'Pincode'}),
        }
