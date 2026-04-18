from django.urls import path
from . import views

urlpatterns = [
    path('', views.liste_rdv, name='liste_rdv'),
    path('prendre/', views.prendre_rdv, name='prendre_rdv'),
    path('prendre/<int:medecin_id>/', views.prendre_rdv, name='prendre_rdv_medecin'),
    path('<int:rdv_id>/', views.detail_rdv, name='detail_rdv'),
    path('<int:rdv_id>/statut/', views.changer_statut, name='changer_statut'),
    path('<int:rdv_id>/annuler/', views.annuler_rdv, name='annuler_rdv'),
    path('agenda/', views.agenda_medecin, name='agenda_medecin'),
    path('agenda/<int:medecin_id>/', views.agenda_medecin, name='agenda_medecin_id'),
    path('creneaux/<int:medecin_id>/', views.creneaux_disponibles, name='creneaux_disponibles'),
    path('statistiques/', views.statistiques, name='statistiques'),
    path('notification/<int:notif_id>/lue/', views.marquer_notif_lue, name='marquer_notif_lue'),
]
