#!/usr/bin/env python
"""
Script de configuration initiale — Clinique Espoir
Crée les comptes de démonstration et les données initiales
Exécuter avec: python setup_demo.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinique_rdv.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import ProfilMedecin, ProfilPatient
from appointments.models import CreneauDisponible, RendezVous
from django.utils import timezone
from datetime import timedelta, time, date
import random

User = get_user_model()

print("🏥 Configuration de Clinique Espoir...")

# ── ADMIN ──
if not User.objects.filter(username='admin').exists():
    admin = User.objects.create_superuser(
        username='admin', password='admin123',
        email='admin@clinique-espoir.ci',
        first_name='Super', last_name='Admin',
        role='admin'
    )
    print("✅ Admin créé: admin / admin123")

# ── MÉDECINS ──
medecins_data = [
    ('Dr. Konan', 'dr.konan', 'medecin123', 'konan@clinique.ci', 'Arnaud', 'Konan', '+225 07 11 22 33', 'Cardiologie', 'MED-001', 15000),
    ('Dr. Touré', 'dr.toure', 'medecin123', 'toure@clinique.ci', 'Fatima', 'Touré', '+225 07 22 33 44', 'Gynécologie', 'MED-002', 12000),
    ('Dr. Koffi', 'dr.koffi', 'medecin123', 'koffi@clinique.ci', 'Jean-Baptiste', 'Koffi', '+225 07 33 44 55', 'Médecine générale', 'MED-003', 8000),
    ('Dr. Bamba', 'dr.bamba', 'medecin123', 'bamba@clinique.ci', 'Ibrahim', 'Bamba', '+225 07 44 55 66', 'Pédiatrie', 'MED-004', 10000),
    ('Dr. Yao', 'dr.yao', 'medecin123', 'yao@clinique.ci', 'Claire', 'Yao', '+225 07 55 66 77', 'Dermatologie', 'MED-005', 10000),
]

medecins_crees = []
for (display, username, password, email, first, last, tel, specialite, ordre, tarif) in medecins_data:
    if not User.objects.filter(username=username).exists():
        user = User.objects.create_user(
            username=username, password=password,
            email=email, first_name=first, last_name=last,
            telephone=tel, role='medecin'
        )
        profil = ProfilMedecin.objects.create(
            user=user, specialite=specialite,
            numero_ordre=ordre, tarif_consultation=tarif,
            disponible=True,
            bio=f"Médecin spécialiste en {specialite} avec plus de 10 ans d'expérience."
        )
        # Créneaux disponibles (Lundi-Vendredi, matin et après-midi)
        for jour in range(5):  # 0=Lundi à 4=Vendredi
            CreneauDisponible.objects.create(
                medecin=profil, jour_semaine=jour,
                heure_debut=time(8, 0), heure_fin=time(12, 0),
                duree_consultation=30, actif=True
            )
            CreneauDisponible.objects.create(
                medecin=profil, jour_semaine=jour,
                heure_debut=time(14, 0), heure_fin=time(17, 30),
                duree_consultation=30, actif=True
            )
        medecins_crees.append(profil)
        print(f"✅ Médecin créé: {username} / {password} — {specialite}")
    else:
        try:
            medecins_crees.append(User.objects.get(username=username).profil_medecin)
        except:
            pass

# ── PATIENTS ──
patients_data = [
    ('patient1', 'patient123', 'Kouadio', 'Emmanuel', 'emmanuel.k@gmail.com', '+225 07 66 77 88', date(1990, 5, 15), 'O+', 'Hypertension artérielle', 'Antécédents familiaux de diabète'),
    ('patient2', 'patient123', 'Diallo', 'Aissatou', 'aissatou.d@gmail.com', '+225 07 77 88 99', date(1985, 8, 22), 'A+', 'Aucune', 'Appendicectomie en 2010'),
    ('patient3', 'patient123', 'N\'Guessan', 'Marc', 'marc.ng@gmail.com', '+225 07 88 99 00', date(2000, 2, 10), 'B+', 'Pénicilline', 'Asthme léger'),
]

patients_crees = []
for (username, password, last, first, email, tel, dob, blood, allergies, antecedents) in patients_data:
    if not User.objects.filter(username=username).exists():
        user = User.objects.create_user(
            username=username, password=password,
            email=email, first_name=first, last_name=last,
            telephone=tel, role='patient'
        )
        ProfilPatient.objects.create(
            user=user, date_naissance=dob,
            groupe_sanguin=blood, allergies=allergies,
            antecedents=antecedents
        )
        patients_crees.append(user)
        print(f"✅ Patient créé: {username} / {password}")
    else:
        patients_crees.append(User.objects.get(username=username))

# ── SECRÉTAIRE ──
if not User.objects.filter(username='secretaire').exists():
    User.objects.create_user(
        username='secretaire', password='secretaire123',
        email='secretaire@clinique.ci',
        first_name='Marie', last_name='Coulibaly',
        role='secretaire'
    )
    print("✅ Secrétaire créée: secretaire / secretaire123")

# ── RENDEZ-VOUS DE DÉMONSTRATION ──
if medecins_crees and patients_crees and RendezVous.objects.count() == 0:
    now = timezone.now()
    rdvs_demo = [
        (patients_crees[0], medecins_crees[0], now + timedelta(days=2, hours=9), 'consultation', 'Bilan cardiaque annuel', 'Palpitations légères', 'confirme'),
        (patients_crees[1], medecins_crees[1], now + timedelta(days=3, hours=10, minutes=30), 'suivi', 'Suivi grossesse', '', 'en_attente'),
        (patients_crees[2], medecins_crees[2], now + timedelta(days=1, hours=14), 'consultation', 'Fièvre et toux persistante', 'Toux sèche depuis 5 jours, fièvre 38.5°C', 'confirme'),
        (patients_crees[0], medecins_crees[2], now - timedelta(days=10, hours=2), 'controle', 'Contrôle tension artérielle', '', 'termine'),
        (patients_crees[1], medecins_crees[0], now - timedelta(days=5, hours=3), 'consultation', 'Douleurs thoraciques', 'Douleur à l\'effort', 'termine'),
        (patients_crees[2], medecins_crees[3], now + timedelta(days=5, hours=16), 'consultation', 'Consultation pédiatrique enfant 3 ans', '', 'en_attente'),
    ]
    for (patient, medecin, dt, type_rdv, motif, symptomes, statut) in rdvs_demo:
        RendezVous.objects.create(
            patient=patient, medecin=medecin, date_heure=dt,
            type_rdv=type_rdv, motif=motif, symptomes=symptomes,
            statut=statut, duree=30
        )
    print(f"✅ {len(rdvs_demo)} rendez-vous de démonstration créés")

print("\n🎉 Configuration terminée !")
print("\n📋 Comptes disponibles:")
print("   Admin       : admin / admin123")
print("   Médecins    : dr.konan, dr.toure, dr.koffi, dr.bamba, dr.yao / medecin123")
print("   Patients    : patient1, patient2, patient3 / patient123")
print("   Secrétaire  : secretaire / secretaire123")
print("\n🚀 Démarrez le serveur: python manage.py runserver")
