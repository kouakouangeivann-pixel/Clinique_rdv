from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Administrateur'),
        ('medecin', 'Médecin'),
        ('secretaire', 'Secrétaire'),
        ('patient', 'Patient'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='patient')
    telephone = models.CharField(max_length=20, blank=True)
    photo = models.ImageField(upload_to='avatars/', blank=True, null=True)

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"

    @property
    def is_medecin(self):
        return self.role == 'medecin'

    @property
    def is_patient(self):
        return self.role == 'patient'

    @property
    def is_secretaire(self):
        return self.role == 'secretaire'

    @property
    def is_admin_role(self):
        return self.role == 'admin'


class ProfilMedecin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profil_medecin')
    specialite = models.CharField(max_length=100)
    numero_ordre = models.CharField(max_length=50, blank=True)
    bio = models.TextField(blank=True)
    tarif_consultation = models.DecimalField(max_digits=8, decimal_places=0, default=5000)
    disponible = models.BooleanField(default=True)

    def __str__(self):
        return f"Dr. {self.user.get_full_name()} - {self.specialite}"


class ProfilPatient(models.Model):
    GROUPE_SANGUIN = [
        ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profil_patient')
    date_naissance = models.DateField(null=True, blank=True)
    groupe_sanguin = models.CharField(max_length=5, choices=GROUPE_SANGUIN, blank=True)
    allergies = models.TextField(blank=True, help_text="Liste des allergies connues")
    antecedents = models.TextField(blank=True, help_text="Antécédents médicaux")
    adresse = models.TextField(blank=True)
    contact_urgence = models.CharField(max_length=100, blank=True)
    tel_urgence = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"Patient: {self.user.get_full_name()}"
