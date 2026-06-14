from django import forms
from django.contrib.auth.models import User
from .models import Item, Request, Review, Category

class UserRegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match")

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['name', 'description', 'category', 'item_type', 'image', 'price']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class RequestForm(forms.ModelForm):
    class Meta:
        model = Request
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optional message to the owner...'}),
        }

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['score', 'comment']
