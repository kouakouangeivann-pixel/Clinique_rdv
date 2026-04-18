from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
import json
from datetime import datetime, timedelta

from .models import RendezVous, CreneauDisponible, Notification, Ordonnance
from accounts.models import ProfilMedecin, User


@login_required
def liste_rdv(request):
    user = request.user
    if user.is_patient:
        rdvs = RendezVous.objects.filter(patient=user).select_related('medecin__user').order_by('-date_heure')
    elif user.is_medecin:
        try:
            rdvs = RendezVous.objects.filter(medecin=user.profil_medecin).select_related('patient').order_by('-date_heure')
        except:
            rdvs = RendezVous.objects.none()
    else:
        rdvs = RendezVous.objects.all().select_related('patient', 'medecin__user').order_by('-date_heure')

    # Filtres
    statut = request.GET.get('statut', '')
    if statut:
        rdvs = rdvs.filter(statut=statut)

    return render(request, 'appointments/liste_rdv.html', {
        'rdvs': rdvs,
        'statut_filter': statut,
        'statut_choices': RendezVous.STATUT_CHOICES,
    })


@login_required
def prendre_rdv(request, medecin_id=None):
    medecins = ProfilMedecin.objects.filter(disponible=True).select_related('user')
    medecin_selectionne = None

    if medecin_id:
        medecin_selectionne = get_object_or_404(ProfilMedecin, id=medecin_id)

    if request.method == 'POST':
        medecin_id_post = request.POST.get('medecin_id')
        date_heure_str = request.POST.get('date_heure')
        type_rdv = request.POST.get('type_rdv', 'consultation')
        motif = request.POST.get('motif', '')
        symptomes = request.POST.get('symptomes', '')

        try:
            medecin = ProfilMedecin.objects.get(id=medecin_id_post)
            # Conversion de la date
            date_heure = datetime.strptime(date_heure_str, '%Y-%m-%dT%H:%M')
            date_heure = timezone.make_aware(date_heure)

            if date_heure <= timezone.now():
                messages.error(request, "La date doit être dans le futur.")
                return redirect('prendre_rdv')

            # Vérifier les conflits
            conflit = RendezVous.objects.filter(
                medecin=medecin,
                date_heure__range=(date_heure - timedelta(minutes=29), date_heure + timedelta(minutes=29)),
                statut__in=['en_attente', 'confirme']
            ).exists()

            if conflit:
                messages.warning(request, "Ce créneau est déjà occupé. Veuillez choisir un autre horaire.")
                return redirect('prendre_rdv')

            rdv = RendezVous.objects.create(
                patient=request.user,
                medecin=medecin,
                date_heure=date_heure,
                type_rdv=type_rdv,
                motif=motif,
                symptomes=symptomes,
                statut='en_attente',
            )

            # Notifier le médecin
            Notification.objects.create(
                destinataire=medecin.user,
                type_notif='rdv_confirme',
                titre='Nouveau rendez-vous',
                message=f"{request.user.get_full_name()} a pris un RDV le {date_heure.strftime('%d/%m/%Y à %H:%M')}",
                rdv=rdv,
            )

            messages.success(request, f"Rendez-vous pris avec succès pour le {date_heure.strftime('%d/%m/%Y à %H:%M')} !")
            return redirect('liste_rdv')

        except (ValueError, ProfilMedecin.DoesNotExist) as e:
            messages.error(request, "Erreur lors de la prise de rendez-vous. Vérifiez les informations.")

    return render(request, 'appointments/prendre_rdv.html', {
        'medecins': medecins,
        'medecin_selectionne': medecin_selectionne,
        'type_choices': RendezVous.TYPE_CHOICES,
    })


@login_required
def detail_rdv(request, rdv_id):
    rdv = get_object_or_404(RendezVous, id=rdv_id)
    # Sécurité: vérifier que l'utilisateur peut voir ce RDV
    user = request.user
    if user.is_patient and rdv.patient != user:
        messages.error(request, "Accès non autorisé.")
        return redirect('liste_rdv')
    if user.is_medecin:
        try:
            if rdv.medecin != user.profil_medecin:
                messages.error(request, "Accès non autorisé.")
                return redirect('liste_rdv')
        except:
            pass

    return render(request, 'appointments/detail_rdv.html', {'rdv': rdv})


@login_required
@require_POST
def changer_statut(request, rdv_id):
    rdv = get_object_or_404(RendezVous, id=rdv_id)
    nouveau_statut = request.POST.get('statut')
    notes = request.POST.get('notes_medecin', '')

    statuts_valides = [s[0] for s in RendezVous.STATUT_CHOICES]
    if nouveau_statut not in statuts_valides:
        messages.error(request, "Statut invalide.")
        return redirect('detail_rdv', rdv_id=rdv_id)

    rdv.statut = nouveau_statut
    if notes:
        rdv.notes_medecin = notes
    rdv.save()

    # Notifier le patient
    msg_map = {
        'confirme': ('rdv_confirme', 'Rendez-vous confirmé', f"Votre RDV du {rdv.date_heure.strftime('%d/%m/%Y à %H:%M')} est confirmé."),
        'annule': ('rdv_annule', 'Rendez-vous annulé', f"Votre RDV du {rdv.date_heure.strftime('%d/%m/%Y à %H:%M')} a été annulé."),
    }
    if nouveau_statut in msg_map:
        type_n, titre, message = msg_map[nouveau_statut]
        Notification.objects.create(
            destinataire=rdv.patient,
            type_notif=type_n,
            titre=titre,
            message=message,
            rdv=rdv,
        )

    messages.success(request, f"Statut mis à jour : {rdv.get_statut_display()}")
    return redirect('detail_rdv', rdv_id=rdv_id)


@login_required
def annuler_rdv(request, rdv_id):
    rdv = get_object_or_404(RendezVous, id=rdv_id)
    if request.user.is_patient and rdv.patient != request.user:
        messages.error(request, "Accès non autorisé.")
        return redirect('liste_rdv')
    if rdv.statut in ['annule', 'termine']:
        messages.warning(request, "Ce rendez-vous ne peut pas être annulé.")
        return redirect('liste_rdv')
    rdv.statut = 'annule'
    rdv.save()
    Notification.objects.create(
        destinataire=rdv.medecin.user,
        type_notif='rdv_annule',
        titre='RDV annulé',
        message=f"{rdv.patient.get_full_name()} a annulé son RDV du {rdv.date_heure.strftime('%d/%m/%Y à %H:%M')}.",
        rdv=rdv,
    )
    messages.success(request, "Rendez-vous annulé.")
    return redirect('liste_rdv')


@login_required
def agenda_medecin(request, medecin_id=None):
    if medecin_id:
        medecin = get_object_or_404(ProfilMedecin, id=medecin_id)
    elif request.user.is_medecin:
        try:
            medecin = request.user.profil_medecin
        except:
            messages.error(request, "Profil médecin introuvable.")
            return redirect('dashboard')
    else:
        messages.error(request, "Accès non autorisé.")
        return redirect('dashboard')

    rdvs = RendezVous.objects.filter(
        medecin=medecin,
        statut__in=['en_attente', 'confirme']
    ).select_related('patient').order_by('date_heure')

    # Format pour FullCalendar JSON
    events = []
    for rdv in rdvs:
        color_map = {
            'en_attente': '#f59e0b',
            'confirme': '#10b981',
            'annule': '#ef4444',
            'termine': '#6b7280',
        }
        events.append({
            'id': rdv.id,
            'title': f"{rdv.patient.get_full_name()} - {rdv.get_type_rdv_display()}",
            'start': rdv.date_heure.isoformat(),
            'end': (rdv.date_heure + timedelta(minutes=rdv.duree)).isoformat(),
            'color': color_map.get(rdv.statut, '#3b82f6'),
            'url': f'/appointments/{rdv.id}/',
            'extendedProps': {
                'statut': rdv.get_statut_display(),
                'motif': rdv.motif,
            }
        })

    return render(request, 'appointments/agenda.html', {
        'medecin': medecin,
        'events_json': json.dumps(events),
        'rdvs': rdvs,
    })


@login_required
def creneaux_disponibles(request, medecin_id):
    """API endpoint: retourne les créneaux libres pour une date donnée"""
    date_str = request.GET.get('date', '')
    if not date_str:
        return JsonResponse({'creneaux': []})

    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'creneaux': []})

    medecin = get_object_or_404(ProfilMedecin, id=medecin_id)
    jour_semaine = date.weekday()

    creneaux = CreneauDisponible.objects.filter(
        medecin=medecin, jour_semaine=jour_semaine, actif=True
    )

    rdvs_du_jour = RendezVous.objects.filter(
        medecin=medecin,
        date_heure__date=date,
        statut__in=['en_attente', 'confirme']
    ).values_list('date_heure__hour', 'date_heure__minute')

    horaires_pris = {(h, m) for h, m in rdvs_du_jour}

    libres = []
    for creneau in creneaux:
        h, m = creneau.heure_debut.hour, creneau.heure_debut.minute
        h_fin, m_fin = creneau.heure_fin.hour, creneau.heure_fin.minute
        duree = creneau.duree_consultation
        current = datetime.combine(date, creneau.heure_debut)
        fin = datetime.combine(date, creneau.heure_fin)
        while current + timedelta(minutes=duree) <= fin:
            if (current.hour, current.minute) not in horaires_pris:
                libres.append(current.strftime('%H:%M'))
            current += timedelta(minutes=duree)

    return JsonResponse({'creneaux': libres, 'date': date_str})


@login_required
def statistiques(request):
    if not (request.user.is_admin_role or request.user.is_secretaire or request.user.is_medecin):
        messages.error(request, "Accès non autorisé.")
        return redirect('dashboard')

    from django.db.models import Count
    from django.db.models.functions import TruncMonth, TruncWeek

    rdvs = RendezVous.objects.all()
    if request.user.is_medecin:
        try:
            rdvs = RendezVous.objects.filter(medecin=request.user.profil_medecin)
        except:
            rdvs = RendezVous.objects.none()

    # RDV par statut
    par_statut = list(rdvs.values('statut').annotate(total=Count('id')))

    # RDV par mois (6 derniers mois)
    par_mois = list(
        rdvs.annotate(mois=TruncMonth('date_heure'))
        .values('mois')
        .annotate(total=Count('id'))
        .order_by('mois')[:6]
    )
    par_mois_data = {
        'labels': [str(m['mois'].strftime('%B %Y')) if m['mois'] else '' for m in par_mois],
        'data': [m['total'] for m in par_mois],
    }

    # RDV par type
    par_type = list(rdvs.values('type_rdv').annotate(total=Count('id')))

    # Top médecins
    top_medecins = list(
        RendezVous.objects.values('medecin__user__first_name', 'medecin__user__last_name', 'medecin__specialite')
        .annotate(total=Count('id'))
        .order_by('-total')[:5]
    )

    return render(request, 'appointments/statistiques.html', {
        'par_statut': par_statut,
        'par_mois': par_mois_data,
        'par_type': par_type,
        'top_medecins': top_medecins,
        'total_rdvs': rdvs.count(),
        'rdvs_confirmes': rdvs.filter(statut='confirme').count(),
        'rdvs_annules': rdvs.filter(statut='annule').count(),
        'rdvs_termines': rdvs.filter(statut='termine').count(),
    })


@login_required
def marquer_notif_lue(request, notif_id):
    from .models import Notification
    notif = get_object_or_404(Notification, id=notif_id, destinataire=request.user)
    notif.lu = True
    notif.save()
    return JsonResponse({'success': True})
