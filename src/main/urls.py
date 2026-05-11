from django.urls import path
from . import views

urlpatterns = [
    path("", views.chat_screen, name='chat_screen'),
    path('api/delete-user/<int:user_id>/', views.delete_user_api)
]
