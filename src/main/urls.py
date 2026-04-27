from django.urls import path
from .views import chat_screen

urlpatterns = [
    path("", chat_screen, name='chat_screen'),
    
]
