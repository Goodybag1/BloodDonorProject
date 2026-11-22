from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import Donor, EmergencyBloodRequest
from .eligibility import (
    is_age_eligible,
    is_donation_interval_eligible,
)


User = get_user_model()


class DonorRegistrationForm(forms.ModelForm):

    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Choose a username',
                'autocomplete': 'username',
            }
        ),
    )

    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Create a password',
                'autocomplete': 'new-password',
            }
        ),
    )

    confirm_password = forms.CharField(
        label='Confirm password',
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Enter your password again',
                'autocomplete': 'new-password',
            }
        ),
    )

    class Meta:
        model = Donor

        fields = [
            'first_name',
            'last_name',
            'date_of_birth',
            'gender',
            'phone_number',
            'email',
            'blood_group',
            'state',
            'city',
            'last_donation_date',
        ]

        error_messages = {
            'phone_number': {
                'unique': (
                    'This phone number is already registered. '
                    'Please use a different number.'
                ),
            },
            'email': {
                'unique': (
                    'This email address is already registered. '
                    'Please use a different email address.'
                ),
            },
        }

        widgets = {
            'first_name': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Enter first name',
                }
            ),
            'last_name': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Enter last name',
                }
            ),
            'date_of_birth': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control',
                }
            ),
            'gender': forms.Select(
                attrs={
                    'class': 'form-select',
                }
            ),
            'phone_number': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Enter phone number',
                }
            ),
            'email': forms.EmailInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Enter email address',
                }
            ),
            'blood_group': forms.Select(
                attrs={
                    'class': 'form-select',
                }
            ),
            'state': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Enter state',
                }
            ),
            'city': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Enter city',
                }
            ),
            'last_donation_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control',
                }
            ),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')

        if username and User.objects.filter(
            username__iexact=username
        ).exists():
            raise forms.ValidationError(
                'This username is already taken. '
                'Please choose another one.'
            )

        return username

    def clean_date_of_birth(self):
        date_of_birth = self.cleaned_data.get(
            'date_of_birth'
        )

        if date_of_birth and not is_age_eligible(
            date_of_birth
        ):
            raise forms.ValidationError(
                'The donor must be between 18 and 65 years old.'
            )

        return date_of_birth

    def clean_last_donation_date(self):
        last_donation_date = self.cleaned_data.get(
            'last_donation_date'
        )

        gender = self.cleaned_data.get('gender')

        if (
            last_donation_date
            and gender
            and not is_donation_interval_eligible(
                last_donation_date,
                gender,
            )
        ):
            if gender.lower() == 'male':
                interval = '12 weeks'
            else:
                interval = '16 weeks'

            raise forms.ValidationError(
                f'The donor must wait at least {interval} '
                'after the previous whole-blood donation.'
            )

        return last_donation_date

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get(
            'confirm_password'
        )

        if password and confirm_password:
            if password != confirm_password:
                self.add_error(
                    'confirm_password',
                    'The passwords do not match.'
                )
            else:
                user = User(
                    username=cleaned_data.get('username'),
                    email=cleaned_data.get('email'),
                    first_name=cleaned_data.get('first_name'),
                    last_name=cleaned_data.get('last_name'),
                )

                try:
                    validate_password(password, user=user)
                except forms.ValidationError as error:
                    self.add_error('password', error)

        return cleaned_data


class EmergencyBloodRequestForm(forms.ModelForm):

    class Meta:
        model = EmergencyBloodRequest

        fields = [
            'requested_blood_group',
            'state',
            'city',
            'request_details',
        ]

        widgets = {
            'requested_blood_group': forms.Select(
                attrs={
                    'class': 'form-select',
                }
            ),
            'state': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Enter state',
                }
            ),
            'city': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Enter city',
                }
            ),
            'request_details': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Describe the emergency blood requirement',
                    'rows': 4,
                }
            ),
        }
