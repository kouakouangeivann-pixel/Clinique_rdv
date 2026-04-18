from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
import json
import urllib.request
import urllib.error


def call_anthropic_api(messages, system_prompt, max_tokens=1000):
    """Appel direct à l'API Anthropic sans bibliothèque externe"""
    api_key = settings.ANTHROPIC_API_KEY
    if not api_key:
        return {"error": "Clé API Anthropic non configurée. Veuillez définir ANTHROPIC_API_KEY dans les settings."}

    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": max_tokens,
        "system": system_prompt,
        "messages": messages,
    }

    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=data,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            return {"text": result["content"][0]["text"]}
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        return {"error": f"Erreur API: {e.code} - {error_body}"}
    except Exception as e:
        return {"error": str(e)}


@login_required
def chatbot_view(request):
    """Page du chatbot médical IA"""
    return render(request, 'ai_assistant/chatbot.html')


@login_required
@require_POST
def chatbot_api(request):
    """Endpoint AJAX pour le chatbot"""
    try:
        body = json.loads(request.body)
        historique = body.get('messages', [])
        message_user = body.get('message', '')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON invalide'}, status=400)

    system_prompt = """Tu es MediBot, l'assistant intelligent de la Clinique Espoir. 
Tu aides les patients avec :
- Des informations générales sur les spécialités médicales et quand consulter
- Des conseils pour préparer leur consultation (documents à apporter, jeûne, etc.)
- Des explications sur le fonctionnement de la clinique et les prises de RDV
- Une orientation vers la bonne spécialité selon les symptômes décrits

RÈGLES IMPORTANTES :
- Tu ne poses JAMAIS de diagnostic médical
- Pour toute urgence, tu dis d'appeler le 15 (SAMU) ou d'aller aux urgences
- Tu rappelles toujours de consulter un médecin pour tout avis médical
- Tu réponds en français, avec empathie et professionnalisme
- Tes réponses sont concises (max 3 paragraphes)
- Tu proposes toujours de prendre un RDV si pertinent

Spécialités disponibles à la clinique : Médecine générale, Cardiologie, Gynécologie, Pédiatrie, Dermatologie, Ophtalmologie, Orthopédie, Neurologie."""

    # Construire les messages pour l'API
    api_messages = [{"role": m["role"], "content": m["content"]} for m in historique[-10:]]
    api_messages.append({"role": "user", "content": message_user})

    result = call_anthropic_api(api_messages, system_prompt)

    if "error" in result:
        return JsonResponse({'error': result["error"]}, status=500)

    return JsonResponse({'response': result["text"]})


@login_required
def analyse_symptomes(request):
    """Page d'analyse des symptômes - suggestion de spécialité"""
    return render(request, 'ai_assistant/analyse_symptomes.html')


@login_required
@require_POST
def analyse_symptomes_api(request):
    """API: analyse les symptômes et suggère une spécialité"""
    try:
        body = json.loads(request.body)
        symptomes = body.get('symptomes', '')
        age = body.get('age', '')
        sexe = body.get('sexe', '')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON invalide'}, status=400)

    if not symptomes:
        return JsonResponse({'error': 'Veuillez décrire vos symptômes.'}, status=400)

    system_prompt = """Tu es un assistant d'orientation médicale. Tu analyses les symptômes décrits et tu suggères :
1. La spécialité médicale la plus adaptée
2. Le niveau d'urgence (URGENCE, RAPIDE dans les 48h, NORMAL dans la semaine, ROUTINE)
3. Des conseils préparatoires pour la consultation
4. Des informations générales (pas de diagnostic)

Réponds UNIQUEMENT en JSON valide avec ce format exact :
{
  "specialite": "Nom de la spécialité",
  "urgence": "URGENCE|RAPIDE|NORMAL|ROUTINE",
  "urgence_couleur": "red|orange|blue|green",
  "message_urgence": "Explication courte",
  "conseils": ["conseil 1", "conseil 2", "conseil 3"],
  "info_generale": "Information générale sur la situation (pas de diagnostic)",
  "disclaimer": "Ce n'est pas un diagnostic médical. Consultez un médecin."
}"""

    user_content = f"Symptômes: {symptomes}"
    if age:
        user_content += f"\nÂge du patient: {age} ans"
    if sexe:
        user_content += f"\nSexe: {sexe}"

    result = call_anthropic_api(
        [{"role": "user", "content": user_content}],
        system_prompt,
        max_tokens=800
    )

    if "error" in result:
        return JsonResponse({'error': result["error"]}, status=500)

    try:
        # Nettoyer et parser le JSON
        text = result["text"].strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        data = json.loads(text.strip())
        return JsonResponse({'success': True, 'analyse': data})
    except json.JSONDecodeError:
        return JsonResponse({'success': True, 'analyse': {'info_generale': result["text"]}})


@login_required
def resume_antecedents(request):
    """Résumé IA des antécédents d'un patient - pour les médecins"""
    if not (request.user.is_medecin or request.user.is_admin_role or request.user.is_secretaire):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden()

    from appointments.models import RendezVous
    from accounts.models import ProfilPatient
    from django.contrib.auth import get_user_model
    User = get_user_model()

    patients = User.objects.filter(role='patient').select_related('profil_patient')
    resume = None
    patient_selectionne = None

    if request.method == 'POST':
        patient_id = request.POST.get('patient_id')
        try:
            patient = User.objects.get(id=patient_id, role='patient')
            patient_selectionne = patient
            rdvs = RendezVous.objects.filter(patient=patient, statut='termine').order_by('-date_heure')[:10]

            historique_text = ""
            for rdv in rdvs:
                historique_text += f"\n- {rdv.date_heure.strftime('%d/%m/%Y')} : {rdv.get_type_rdv_display()} avec Dr.{rdv.medecin.user.last_name} ({rdv.medecin.specialite})"
                if rdv.motif:
                    historique_text += f" | Motif: {rdv.motif}"
                if rdv.notes_medecin:
                    historique_text += f" | Notes: {rdv.notes_medecin}"

            try:
                profil = patient.profil_patient
                antecedents_text = profil.antecedents or "Non renseigné"
                allergies_text = profil.allergies or "Aucune connue"
                groupe_sanguin = profil.groupe_sanguin or "Non renseigné"
            except:
                antecedents_text = "Non renseigné"
                allergies_text = "Aucune connue"
                groupe_sanguin = "Non renseigné"

            system_prompt = """Tu es un assistant médical. Génère un résumé clinique structuré et professionnel 
du dossier patient pour aider le médecin à préparer sa consultation.
Le résumé doit être concis, en langage médical approprié, organisé en sections claires.
Insiste sur les points importants et les tendances observées."""

            user_content = f"""Patient: {patient.get_full_name()}, {patient.profil_patient.date_naissance if hasattr(patient, 'profil_patient') and patient.profil_patient.date_naissance else 'âge non renseigné'}
Groupe sanguin: {groupe_sanguin}
Allergies: {allergies_text}
Antécédents médicaux: {antecedents_text}
Historique des consultations:{historique_text if historique_text else " Aucune consultation enregistrée."}

Génère un résumé clinique structuré pour la prochaine consultation."""

            result = call_anthropic_api(
                [{"role": "user", "content": user_content}],
                system_prompt,
                max_tokens=1200
            )
            resume = result.get("text") or result.get("error", "Erreur lors de la génération.")
        except User.DoesNotExist:
            resume = "Patient introuvable."

    return render(request, 'ai_assistant/resume_antecedents.html', {
        'patients': patients,
        'resume': resume,
        'patient_selectionne': patient_selectionne,
    })


@login_required
@require_POST
def suggestion_creneaux_api(request):
    """IA suggère les meilleurs créneaux selon les préférences du patient"""
    try:
        body = json.loads(request.body)
        medecin_id = body.get('medecin_id')
        preferences = body.get('preferences', '')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON invalide'}, status=400)

    from appointments.models import CreneauDisponible, RendezVous
    from accounts.models import ProfilMedecin
    from datetime import date, timedelta

    try:
        medecin = ProfilMedecin.objects.get(id=medecin_id)
    except ProfilMedecin.DoesNotExist:
        return JsonResponse({'error': 'Médecin introuvable'}, status=404)

    # Récupérer les créneaux disponibles
    creneaux = CreneauDisponible.objects.filter(medecin=medecin, actif=True)
    creneaux_info = [f"{c.get_jour_semaine_display()} {c.heure_debut}-{c.heure_fin}" for c in creneaux]

    # RDV déjà pris cette semaine
    rdvs_semaine = RendezVous.objects.filter(
        medecin=medecin,
        date_heure__gte=date.today(),
        date_heure__lte=date.today() + timedelta(days=14),
        statut__in=['en_attente', 'confirme']
    ).values_list('date_heure', flat=True)

    rdvs_pris = [str(r.strftime('%A %d/%m à %H:%M')) for r in rdvs_semaine]

    system_prompt = """Tu es un assistant de planification médicale. 
En fonction des créneaux disponibles du médecin et des préférences du patient, 
suggère 3 créneaux optimaux pour les 2 prochaines semaines.
Réponds en JSON : {"suggestions": [{"date": "Lundi 15/01", "heure": "09:00", "raison": "..."}]}"""

    user_content = f"""Médecin: Dr. {medecin.user.get_full_name()} ({medecin.specialite})
Créneaux habituels: {', '.join(creneaux_info) if creneaux_info else 'Non définis'}
RDV déjà pris: {', '.join(rdvs_pris) if rdvs_pris else 'Aucun'}
Préférences du patient: {preferences or 'Aucune préférence particulière'}
Date actuelle: {date.today().strftime('%d/%m/%Y')}

Suggère 3 créneaux optimaux."""

    result = call_anthropic_api(
        [{"role": "user", "content": user_content}],
        system_prompt,
        max_tokens=600
    )

    if "error" in result:
        return JsonResponse({'error': result["error"]}, status=500)

    try:
        text = result["text"].strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        data = json.loads(text.strip())
        return JsonResponse({'success': True, 'suggestions': data.get('suggestions', [])})
    except:
        return JsonResponse({'success': True, 'suggestions': [], 'raw': result["text"]})
