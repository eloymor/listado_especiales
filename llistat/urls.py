from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'llistat'

urlpatterns = [
    path('', views.upload_csv, name='upload_csv'),
    path('report/', views.report, name='report'),
    path('login', views.user_login, name='login'),
    path('logout', auth_views.LogoutView.as_view(), name='logout'),
]
