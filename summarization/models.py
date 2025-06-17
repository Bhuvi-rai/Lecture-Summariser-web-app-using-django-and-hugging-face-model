from django.db import models

class Lecture(models.Model):
    title = models.CharField(max_length=100, default='Untitled')
    lecture_file = models.FileField(upload_to='lectures/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

class DetailedNotes(models.Model):
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE)
    notes = models.TextField()
