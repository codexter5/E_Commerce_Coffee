from django import forms

from core.form_utils import apply_bootstrap_styles
from .models import Review


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ("rating", "comment")
        widgets = {
            "comment": forms.Textarea(attrs={"rows": 4, "placeholder": "Share your thoughts about this product..."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_bootstrap_styles(self)

    def clean_rating(self):
        value = self.cleaned_data["rating"]
        if not 1 <= value <= 5:
            raise forms.ValidationError("Rating must be between 1 and 5.")
        return value
