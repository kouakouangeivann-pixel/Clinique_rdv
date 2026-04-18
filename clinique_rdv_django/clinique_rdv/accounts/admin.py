from django.contrib import admin
from .models import User, ProfilMedecin, ProfilPatient


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'get_full_name', 'role', 'email', 'telephone', 'is_active']
    list_filter = ['role', 'is_active']
    search_fields = ['username', 'first_name', 'last_name', 'email']


@admin.register(ProfilMedecin)
class ProfilMedecinAdmin(admin.ModelAdmin):
    list_display = ['user', 'specialite', 'tarif_consultation', 'disponible']
    list_filter = ['specialite', 'disponible']


@admin.register(ProfilPatient)
class ProfilPatientAdmin(admin.ModelAdmin):
    list_display = ['user', 'date_naissance', 'groupe_sanguin']
