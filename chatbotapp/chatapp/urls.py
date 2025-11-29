# chatapp/urls.py
from django.urls import path
from . import views

app_name = 'chatapp'

urlpatterns = [
    path('', views.index, name='index'),
    path('api/chat/', views.chat_api, name='chat_api'),
    path('api/history/', views.history_api, name='history_api'),
    path('api/quit/', views.quit_api, name='quit_api'),
]
