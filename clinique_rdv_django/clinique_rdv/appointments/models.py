from django.db import models
from django.utils import timezone
from accounts.models import User, ProfilMedecin


class CreneauDisponible(models.Model):
    JOURS = [
        (0, 'Lundi'), (1, 'Mardi'), (2, 'Mercredi'),
        (3, 'Jeudi'), (4, 'Vendredi'), (5, 'Samedi'), (6, 'Dimanche'),
    ]
    medecin = models.ForeignKey(ProfilMedecin, on_delete=models.CASCADE, related_name='creneaux')
    jour_semaine = models.IntegerField(choices=JOURS)
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    duree_consultation = models.IntegerField(default=30, help_text="Durée en minutes")
    actif = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Créneau disponible"
        ordering = ['jour_semaine', 'heure_debut']

    def __str__(self):
        return f"{self.get_jour_semaine_display()} {self.heure_debut}-{self.heure_fin} ({self.medecin})"


class RendezVous(models.Model):
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('confirme', 'Confirmé'),
        ('annule', 'Annulé'),
        ('termine', 'Terminé'),
        ('absent', 'Patient absent'),
    ]
    TYPE_CHOICES = [
        ('consultation', 'Consultation'),
        ('suivi', 'Suivi'),
        ('urgence', 'Urgence'),
        ('controle', 'Contrôle'),
    ]

    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rdv_patient')
    medecin = models.ForeignKey(ProfilMedecin, on_delete=models.CASCADE, related_name='rdv_medecin')
    date_heure = models.DateTimeField()
    duree = models.IntegerField(default=30, help_text="Durée en minutes")
    type_rdv = models.CharField(max_length=20, choices=TYPE_CHOICES, default='consultation')
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    motif = models.TextField(help_text="Motif de la consultation")
    notes_medecin = models.TextField(blank=True, help_text="Notes du médecin (post-consultation)")
    symptomes = models.TextField(blank=True, help_text="Symptômes décrits par le patient")
    rappel_envoye = models.BooleanField(default=False)
    cree_le = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Rendez-vous"
        verbose_name_plural = "Rendez-vous"
        ordering = ['-date_heure']

    def __str__(self):
        return f"RDV {self.patient.get_full_name()} - Dr.{self.medecin.user.last_name} le {self.date_heure.strftime('%d/%m/%Y %H:%M')}"

    @property
    def is_past(self):
        return self.date_heure < timezone.now()

    @property
    def badge_class(self):
        classes = {
            'en_attente': 'badge-warning',
            'confirme': 'badge-info',
            'annule': 'badge-danger',
            'termine': 'badge-success',
            'absent': 'badge-secondary',
        }
        return classes.get(self.statut, 'badge-secondary')


class Ordonnance(models.Model):
    rendez_vous = models.OneToOneField(RendezVous, on_delete=models.CASCADE, related_name='ordonnance')
    contenu = models.TextField()
    date_emission = models.DateField(auto_now_add=True)
    valide_jusqu = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Ordonnance du {self.date_emission} - {self.rendez_vous.patient.get_full_name()}"


class Notification(models.Model):
    TYPE_CHOICES = [
        ('rdv_confirme', 'RDV Confirmé'),
        ('rdv_annule', 'RDV Annulé'),
        ('rappel', 'Rappel RDV'),
        ('info', 'Information'),
    ]
    destinataire = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type_notif = models.CharField(max_length=20, choices=TYPE_CHOICES)
    titre = models.CharField(max_length=200)
    message = models.TextField()
    lu = models.BooleanField(default=False)
    cree_le = models.DateTimeField(auto_now_add=True)
    rdv = models.ForeignKey(RendezVous, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-cree_le']

    def __str__(self):
        return f"Notif pour {self.destinataire} - {self.titre}"
