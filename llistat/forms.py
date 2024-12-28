from django import forms
from .models import CSVFile


class CSVFileUploadForm(forms.ModelForm):
    class Meta:
        model = CSVFile
        fields = ['file']  # Only show the FileField in the form
