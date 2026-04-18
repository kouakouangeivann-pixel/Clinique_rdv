from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, ProfilPatient, ProfilMedecin


class LoginForm(forms.Form):
    username = forms.CharField(
        label="Nom d'utilisateur",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Nom d'utilisateur"})
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Mot de passe'})
    )


class PatientRegisterForm(UserCreationForm):
    first_name = forms.CharField(label="Prénom", widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label="Nom", widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={'class': 'form-control'}))
    telephone = forms.CharField(label="Téléphone", widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'telephone', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['class'] = 'form-control'


class MedecinRegisterForm(UserCreationForm):
    first_name = forms.CharField(label="Prénom", widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label="Nom", widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={'class': 'form-control'}))
    telephone = forms.CharField(label="Téléphone", widget=forms.TextInput(attrs={'class': 'form-control'}))
    specialite = forms.CharField(label="Spécialité", widget=forms.TextInput(attrs={'class': 'form-control'}))
    numero_ordre = forms.CharField(label="N° Ordre Médecins", widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'telephone', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['class'] = 'form-control'

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'medecin'
        if commit:
            user.save()
            ProfilMedecin.objects.create(
                user=user,
                specialite=self.cleaned_data['specialite'],
                numero_ordre=self.cleaned_data['numero_ordre'],
            )
        return user


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'telephone', 'photo']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
        }


class RendezVousForm(forms.Form):
    """Formulaire de prise de RDV pour les patients"""
    from appointments.models import RendezVous
    medecin_id = forms.IntegerField(widget=forms.HiddenInput())
    date_heure = forms.DateTimeField(
        label="Date et heure",
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        input_formats=['%Y-%m-%dT%H:%M']
    )
    type_rdv = forms.ChoiceField(
        label="Type de consultation",
        choices=RendezVous.TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    motif = forms.CharField(
        label="Motif de consultation",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    symptomes = forms.CharField(
        label="Symptômes (optionnel)",
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
