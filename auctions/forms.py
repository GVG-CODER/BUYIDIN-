from django import forms
from . models import payments
from crispy_forms.layout import Layout, Submit
from crispy_forms.helper import FormHelper

class PaymentForm(forms.ModelForm):
    class meta :
        model = payments
        fields = "__all__"

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.helper = FormHelper(self)
            self.helper.layout = Layout(
                'name',
                'Amount',
                Submit('submit','Make payment', css_class="button white btn-block btn-primary"),
            )