# orders/forms.py
from django import forms
from .models import Order

class TrackingForm(forms.ModelForm):
    class Meta:
        model = Order
        # Si tu modelo tiene 'tracking_code' y 'status':
        fields = ["tracking_code", "status"]
        # Si tu modelo usa 'tracking' en lugar de 'tracking_code', usa:
        # fields = ["tracking", "status"]

        widgets = {
            # Cambia la clave según el campo real:
            "tracking_code": forms.TextInput(attrs={"placeholder": "GB-XXXX...", "class": "input"}),
            # "tracking": forms.TextInput(attrs={"placeholder": "GB-XXXX...", "class": "input"}),
            "status": forms.Select(attrs={"class": "input"}),
        }
