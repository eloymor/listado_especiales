from django.urls import path
from . import views

app_name = 'llistat'

urlpatterns = [
    path('', views.upload_csv, name='upload_csv'),
    path('report/', views.report, name='report'),
]
