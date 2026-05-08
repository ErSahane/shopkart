from django import forms
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm
from django.contrib.auth.models import User

from .models import Address, Product, Review


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=80)
    last_name = forms.CharField(max_length=80, required=False)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email


class OTPForm(forms.Form):
    code = forms.CharField(max_length=6, min_length=6, label='Verification code')


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        exclude = ['user']


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'title', 'comment']
        widgets = {'rating': forms.NumberInput(attrs={'min': 1, 'max': 5})}


class CheckoutForm(forms.Form):
    payment_method = forms.ChoiceField(choices=[('cod', 'Cash on Delivery'), ('gateway', 'Online Payment')])
    address_id = forms.IntegerField(widget=forms.HiddenInput, required=False)
    coupon_code = forms.CharField(max_length=40, required=False)


class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'category', 'name', 'description', 'price', 'compare_at_price', 'image',
            'gallery_image_1', 'gallery_image_2', 'stock', 'is_active', 'is_featured', 'is_trending',
        ]


class SearchForm(forms.Form):
    q = forms.CharField(required=False)
    category = forms.CharField(required=False)
    min_price = forms.DecimalField(required=False, min_value=0)
    max_price = forms.DecimalField(required=False, min_value=0)
    sort = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Featured'),
            ('price_asc', 'Price: low to high'),
            ('price_desc', 'Price: high to low'),
            ('newest', 'Newest'),
            ('rating', 'Top rated'),
        ],
    )
