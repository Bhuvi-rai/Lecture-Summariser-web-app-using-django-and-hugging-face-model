from django.urls import path
from . import views

urlpatterns = [
    path('', views.upload_lecture, name='upload'),
    path('notes/<int:lecture_id>/', views.view_notes, name='notes'),
]
