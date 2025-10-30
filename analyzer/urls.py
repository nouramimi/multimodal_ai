"""
URLs pour l'application analyzer
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_view, name='chat_view'),
    
    path('send/', views.send_message, name='send_message'), 
    path('send-message/', views.send_message, name='send_message_alt'), 
    path('history/', views.get_history, name='get_history'),
    path('clear/', views.clear_history, name='clear_history'),  
    path('clear-history/', views.clear_history, name='clear_history_alt'), 
    
    # Test endpoint (optionnel)
    path('test-chatbot/', views.test_chatbot, name='test_chatbot'),
]