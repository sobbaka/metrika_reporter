from django import forms
from django.forms import EmailInput, TextInput, NumberInput

from .models import Project


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'email', 'counter', 'token']

        widgets = {
            'name': TextInput(attrs={"class": "form-control"}),
            'email': EmailInput(attrs={"class": "form-control"}),
            'counter': NumberInput(attrs={"class": "form-control"}),
            'token': TextInput(attrs={"class": "form-control"}),
        }


class ProjectCreateForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'email', 'counter', 'token']

        widgets = {
            'name': TextInput(attrs={"class": "form-control"}),
            'email': EmailInput(attrs={"class": "form-control"}),
            'counter': NumberInput(attrs={"class": "form-control"}),
            'token': TextInput(attrs={"class": "form-control"}),
        }