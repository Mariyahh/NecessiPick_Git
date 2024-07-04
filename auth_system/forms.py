from django import forms
from .models import UserProfile
from django.contrib.auth.models import User
from datetime import date



class ProfilePictureForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['profile_picture']


#

class UserProfileForm(forms.ModelForm):
     
     GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    )
     gender = forms.ChoiceField(choices=GENDER_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
     birthday = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
     age = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'form-control'}))
     purpose = forms.ChoiceField(choices=[('Budget', 'To Find Cheap Products'), ('Student', 'As a Boarding Student'), ('Party', 'Preparing for a Party'), ('Other', 'Other')], widget=forms.Select(attrs={'class': 'form-control'}))
    
    # Add other fields here
     class Meta:
        model = UserProfile
        fields = ['gender', 'birthday', 'age', 'purpose', 'region', 'city']

    #  def clean_birthday(self):
    #     # Calculate age based on the entered birthday
    #     birthday = self.cleaned_data.get('birthday')
    #     if birthday:
    #         today = date.today()
    #         age = today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))
    #         self.cleaned_data['age'] = age
    #     return birthday



class UpdateNameForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']
