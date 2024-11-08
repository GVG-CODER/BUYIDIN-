from django import forms
from . models import payments
from crispy_forms.layout import Layout, Submit
from crispy_forms.helper import FormHelper

class PaymentForm(forms.ModelForm):
    class Meta:  # Correct capitalization
        model = payments # Ensure this matches your model class name
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            'name',
            'amount',  # Make sure field names match your model exactly (e.g., 'amount' not 'Amount')
            Submit('submit', 'Make Payment', css_class="button white btn-block btn-primary")
        )