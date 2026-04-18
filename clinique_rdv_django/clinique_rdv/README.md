# 🏥 Clinique Espoir — Application de Gestion des Rendez-vous
### Projet de fin de licence en Informatique — Option Génie Logiciel

---

## 📋 Description du projet

Application web Django complète pour la gestion des rendez-vous médicaux d'une clinique, enrichie par un module d'Intelligence Artificielle (IA) propulsé par Claude d'Anthropic.

---

## ✨ Fonctionnalités

### 🗓️ Gestion des Rendez-vous
- Prise de RDV en ligne par les patients
- Confirmation, modification et annulation
- Détection automatique des conflits de créneaux
- Système de notifications automatiques
- Agenda interactif (FullCalendar) pour les médecins

### 👥 Gestion Multi-rôles
| Rôle | Accès |
|------|-------|
| **Patient** | Prendre RDV, voir ses consultations, utiliser l'IA |
| **Médecin** | Gérer agenda, confirmer RDV, notes médicales |
| **Secrétaire** | Vue globale, gestion des RDV |
| **Admin** | Accès complet + interface Django Admin |

### 🤖 Modules d'Intelligence Artificielle (Claude AI)
1. **MediBot** — Chatbot assistant disponible 24h/24
   - Répond aux questions générales sur la santé
   - Oriente vers la bonne spécialité médicale
   - Aide à préparer les consultations (documents, jeûne, etc.)
   - Explique le fonctionnement de la clinique

2. **Analyse de Symptômes** — Orientation médicale intelligente
   - Analyse les symptômes décrits en langage naturel
   - Détermine le niveau d'urgence (URGENCE / RAPIDE / NORMAL / ROUTINE)
   - Suggère la spécialité médicale appropriée
   - Produit des conseils personnalisés

3. **Résumé de Dossier Patient** — Aide à la décision médicale
   - Génère un résumé clinique structuré des antécédents
   - Synthétise l'historique des consultations passées
   - Met en évidence les points d'attention cliniques
   - Aide les médecins à préparer leurs consultations

### 📊 Statistiques & Tableaux de bord
- Graphiques Chart.js (évolution mensuelle, répartition par statut, par type)
- Top médecins par activité
- KPIs en temps réel par rôle

---

## 🛠️ Installation

### 1. Prérequis
```
Python 3.10+
pip
```

### 2. Installer les dépendances
```bash
cd clinique_rdv
pip install -r requirements.txt
```

### 3. Appliquer les migrations
```bash
python manage.py makemigrations accounts
python manage.py makemigrations appointments
python manage.py makemigrations ai_assistant
python manage.py makemigrations core
python manage.py migrate
```

### 4. Charger les données de démonstration
```bash
python setup_demo.py
```

### 5. Configurer la clé API Anthropic (pour l'IA)
```bash
# Windows
set ANTHROPIC_API_KEY=sk-ant-xxxxxx

# Linux / Mac
export ANTHROPIC_API_KEY=sk-ant-xxxxxx
```
> Obtenez votre clé sur https://console.anthropic.com

### 6. Lancer le serveur de développement
```bash
python manage.py runserver
```
Accédez à : **http://127.0.0.1:8000**

---

## 🔐 Comptes de démonstration

| Rôle | Identifiant | Mot de passe |
|------|-------------|--------------|
| Administrateur | `admin` | `admin123` |
| Médecin Cardiologue | `dr.konan` | `medecin123` |
| Médecin Gynécologue | `dr.toure` | `medecin123` |
| Médecin Généraliste | `dr.koffi` | `medecin123` |
| Pédiatre | `dr.bamba` | `medecin123` |
| Dermatologue | `dr.yao` | `medecin123` |
| Patient | `patient1` | `patient123` |
| Secrétaire | `secretaire` | `secretaire123` |

---

## 🏗️ Architecture du projet

```
clinique_rdv/
├── clinique_rdv/          # Configuration Django
│   ├── settings.py        # Paramètres (DB, auth, IA)
│   └── urls.py            # Routage principal
├── accounts/              # Utilisateurs & profils
│   ├── models.py          # User, ProfilMedecin, ProfilPatient
│   ├── views.py           # Login, register, dashboard
│   └── forms.py           # Formulaires
├── appointments/          # Rendez-vous
│   ├── models.py          # RendezVous, Creneau, Notification
│   └── views.py           # CRUD RDV, agenda, statistiques
├── ai_assistant/          # Modules IA
│   └── views.py           # Chatbot, analyse symptômes, résumé
├── templates/             # Interface HTML
│   ├── base.html          # Layout avec sidebar
│   ├── accounts/          # Login, dashboard, profil, médecins
│   ├── appointments/      # Liste RDV, agenda, stats, détail
│   └── ai_assistant/      # Chatbot, analyse, résumé dossier
├── requirements.txt
└── setup_demo.py          # Script de données de démonstration
```

---

## 🎨 Technologies utilisées

| Technologie | Rôle |
|-------------|------|
| **Django 4.2** | Framework web Python |
| **SQLite** | Base de données |
| **HTML / CSS / JS** | Frontend natif |
| **Chart.js** | Graphiques & statistiques |
| **FullCalendar 5** | Agenda interactif |
| **Font Awesome 6** | Icônes |
| **Claude AI (Anthropic)** | Intelligence artificielle |

---

## 🎓 Informations soutenance

- **Thème** : Application de gestion de rendez-vous — cas d'une clinique
- **Filière** : Informatique — Génie Logiciel (Licence)
- **Spécificité** : Intégration d'un module IA (Claude d'Anthropic) pour l'assistance aux patients et aux médecins
