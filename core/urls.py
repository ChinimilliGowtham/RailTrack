from django.urls import path
from . import views

urlpatterns = [
    path('', views.welcome, name='welcome'),
    path('register/', views.register_user, name='register_user'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('crowd-info/', views.crowd_info, name='crowd_info'),
    path('logout/', views.logout_view, name='logout'),
    path('recents/', views.recents, name='recents'),
    path('coach-layout/', views.coach_layout, name='coach_layout'),
    path('trains-at-station/', views.trains_at_station, name='trains_at_station'),
]