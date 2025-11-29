# chatbotapp/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # root will serve the chat app
    path('', include('chatapp.urls', namespace='chatapp')),
]
