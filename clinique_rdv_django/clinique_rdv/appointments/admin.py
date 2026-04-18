from django.contrib import admin
from .models import RendezVous, CreneauDisponible, Notification, Ordonnance


@admin.register(RendezVous)
class RendezVousAdmin(admin.ModelAdmin):
    list_display = ['patient', 'medecin', 'date_heure', 'type_rdv', 'statut']
    list_filter = ['statut', 'type_rdv', 'medecin']
    search_fields = ['patient__username', 'patient__first_name', 'medecin__user__last_name']
    date_hierarchy = 'date_heure'


@admin.register(CreneauDisponible)
class CreneauAdmin(admin.ModelAdmin):
    list_display = ['medecin', 'get_jour_semaine_display', 'heure_debut', 'heure_fin', 'actif']
    list_filter = ['medecin', 'actif', 'jour_semaine']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['destinataire', 'type_notif', 'titre', 'lu', 'cree_le']
    list_filter = ['type_notif', 'lu']
