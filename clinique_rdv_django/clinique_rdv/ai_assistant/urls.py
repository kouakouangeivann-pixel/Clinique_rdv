from django.urls import path
from . import views

urlpatterns = [
    path('chatbot/', views.chatbot_view, name='chatbot'),
    path('chatbot/api/', views.chatbot_api, name='chatbot_api'),
    path('symptomes/', views.analyse_symptomes, name='analyse_symptomes'),
    path('symptomes/api/', views.analyse_symptomes_api, name='analyse_symptomes_api'),
    path('resume/', views.resume_antecedents, name='resume_antecedents'),
    path('creneaux/suggestion/', views.suggestion_creneaux_api, name='suggestion_creneaux_api'),
]
