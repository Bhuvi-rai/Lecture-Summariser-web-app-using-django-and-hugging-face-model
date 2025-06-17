from django import forms
from .models import Lecture

class LectureUploadForm(forms.ModelForm):
    class Meta:
        model = Lecture
        fields = ['lecture_file']
