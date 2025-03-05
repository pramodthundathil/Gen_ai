from django.contrib.auth.models import User 
from django.contrib.auth.forms import UserCreationForm , UserChangeForm
from .models import CustomUser
from django import forms


class UserAddForm(UserCreationForm):
    class Meta:
        model = CustomUser 
        # fields = "__all__"
        fields = ["email","phone","address","company_logo","company_name","website","password1","password2"]


        widgets = {
            "address":forms.Textarea(attrs={"class":"form-control", "placeholder":"Username"}),
            "phone":forms.NumberInput(attrs={"class":"form-control","placeholder":"Phone Number"}),
            "company_logo":forms.FileInput(attrs={"class":"form-control"}),
            "email":forms.EmailInput(attrs={"class":"form-control","placeholder":"Email"}),
            "company_name":forms.TextInput(attrs={"class":"form-control", "placeholder":"Company Name"}),
            "website":forms.TextInput(attrs={"class":"form-control", "placeholder":"Website"}),
        
        }

    def __init__(self, *args, **kwargs):
        super(UserAddForm, self).__init__(*args, **kwargs)
        self.fields['password1'].widget = forms.PasswordInput(attrs={'class': 'form-control  py-3', 'placeholder': 'Password'})
        self.fields['password2'].widget = forms.PasswordInput(attrs={'class': 'form-control  py-3', 'placeholder': 'Password confirmation'})


class UserUpdateForm(UserChangeForm):
    class Meta:
        model = CustomUser 
        # fields = "__all__"
        fields = ["email","phone","address","company_logo","company_name","website","password"]


        widgets = {
            "address":forms.Textarea(attrs={"class":"form-control", "placeholder":"Username"}),
            "phone":forms.NumberInput(attrs={"class":"form-control","placeholder":"Phone Number"}),
            "company_logo":forms.FileInput(attrs={"class":"form-control"}),
            "email":forms.EmailInput(attrs={"class":"form-control","placeholder":"Email"}),
            "company_name":forms.TextInput(attrs={"class":"form-control", "placeholder":"Company Name"}),
            "website":forms.TextInput(attrs={"class":"form-control", "placeholder":"Website"}),
        
        }

    def __init__(self, *args, **kwargs):
        super(UserUpdateForm, self).__init__(*args, **kwargs)
        self.fields['password'].widget = forms.PasswordInput(attrs={'class': 'form-control  py-3', 'placeholder': 'Password'})




       
