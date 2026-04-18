from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import User, ProfilMedecin, ProfilPatient
from .forms import LoginForm, PatientRegisterForm, ProfileUpdateForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, f"Bienvenue, {user.get_full_name()} !")
            return redirect(request.GET.get('next', 'dashboard'))
        else:
            messages.error(request, "Identifiants incorrects.")
    return render(request, 'accounts/login.html', {})


def logout_view(request):
    logout(request)
    return redirect('home')


def register_patient(request):
    form = PatientRegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        user.role = 'patient'
        user.save()
        ProfilPatient.objects.create(user=user)
        login(request, user)
        messages.success(request, "Compte créé avec succès ! Bienvenue à la Clinique Espoir.")
        return redirect('dashboard')
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def dashboard(request):
    user = request.user
    context = {'user': user}
    now = timezone.now()
    from appointments.models import RendezVous, Notification

    if user.is_patient:
        rdvs = RendezVous.objects.filter(patient=user).order_by('date_heure')
        context['prochains_rdvs'] = rdvs.filter(
            date_heure__gte=now, statut__in=['en_attente', 'confirme'])[:5]
        context['rdvs_passes'] = rdvs.filter(date_heure__lt=now).count()
        context['rdvs_a_venir'] = rdvs.filter(
            date_heure__gte=now, statut__in=['en_attente', 'confirme']).count()
        context['rdvs_termines'] = rdvs.filter(statut='termine').count()
    elif user.is_medecin:
        try:
            profil = user.profil_medecin
            rdvs = RendezVous.objects.filter(medecin=profil).order_by('date_heure')
            context['prochains_rdvs'] = rdvs.filter(
                date_heure__gte=now, statut__in=['en_attente', 'confirme'])[:8]
            context['rdvs_aujourd_hui'] = rdvs.filter(
                date_heure__date=now.date(), statut__in=['en_attente', 'confirme'])
            context['total_patients'] = rdvs.values('patient').distinct().count()
            context['profil'] = profil
        except ProfilMedecin.DoesNotExist:
            pass
    else:
        rdvs = RendezVous.objects.all().order_by('date_heure')
        context['prochains_rdvs'] = rdvs.filter(
            date_heure__gte=now, statut__in=['en_attente', 'confirme'])[:10]
        context['rdvs_aujourd_hui'] = rdvs.filter(date_heure__date=now.date()).count()
        context['total_rdvs'] = rdvs.count()
        context['rdvs_en_attente'] = rdvs.filter(statut='en_attente').count()
        context['medecins_dispo'] = ProfilMedecin.objects.filter(disponible=True).count()

    context['notifications'] = Notification.objects.filter(destinataire=user, lu=False)[:5]
    context['nb_notifs'] = Notification.objects.filter(destinataire=user, lu=False).count()
    return render(request, 'accounts/dashboard.html', context)


@login_required
def profile_view(request):
    user = request.user
    form = ProfileUpdateForm(request.POST or None, request.FILES or None, instance=user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        if user.is_patient:
            profil, _ = ProfilPatient.objects.get_or_create(user=user)
            profil.date_naissance = request.POST.get('date_naissance') or None
            profil.groupe_sanguin = request.POST.get('groupe_sanguin', '')
            profil.allergies = request.POST.get('allergies', '')
            profil.antecedents = request.POST.get('antecedents', '')
            profil.adresse = request.POST.get('adresse', '')
            profil.contact_urgence = request.POST.get('contact_urgence', '')
            profil.tel_urgence = request.POST.get('tel_urgence', '')
            profil.save()
        messages.success(request, "Profil mis à jour avec succès.")
        return redirect('profile')
    profil_patient = None
    if user.is_patient:
        profil_patient, _ = ProfilPatient.objects.get_or_create(user=user)
    return render(request, 'accounts/profile.html', {'form': form, 'profil_patient': profil_patient})


@login_required
def medecins_list(request):
    specialite = request.GET.get('specialite', '')
    medecins = ProfilMedecin.objects.filter(disponible=True).select_related('user')
    if specialite:
        medecins = medecins.filter(specialite__icontains=specialite)
    specialites = ProfilMedecin.objects.filter(disponible=True).values_list('specialite', flat=True).distinct()
    return render(request, 'accounts/medecins.html', {
        'medecins': medecins,
        'specialites': specialites,
        'specialite_filter': specialite,
    })
