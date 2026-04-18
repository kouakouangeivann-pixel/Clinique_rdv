from django.shortcuts import render, redirect
from accounts.models import ProfilMedecin


def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    medecins = ProfilMedecin.objects.filter(disponible=True).select_related('user')[:6]
    return render(request, 'core/home.html', {'medecins': medecins})
