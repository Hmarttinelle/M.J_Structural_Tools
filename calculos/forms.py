# calculos/forms.py
from django import forms
from .models import SystemConfiguration


class SystemConfigurationForm(forms.ModelForm):
    """
    Formulário de configuração visual da aplicação.

    Os dois campos de imagem são declarados explicitamente para garantir que
    são sempre ligados a request.FILES e disponibilizados no template.
    """

    background_image = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(
            attrs={
                "accept": "image/png,image/jpeg,image/webp",
                "class": "config-file-input",
            }
        ),
        label="Imagem de Fundo",
    )

    sidebar_image = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(
            attrs={
                "accept": "image/png,image/jpeg,image/webp",
                "class": "config-file-input",
            }
        ),
        label="Imagem da Barra Lateral",
    )

    class Meta:
        model = SystemConfiguration
        fields = [
            "theme_mode",
            "primary_color",
            "background_image",
            "sidebar_image",
        ]

        labels = {
            "theme_mode": "Modo do Tema",
            "primary_color": "Cor Principal da Interface",
            "background_image": "Imagem de Fundo",
            "sidebar_image": "Imagem da Barra Lateral",
        }

        widgets = {
            "theme_mode": forms.RadioSelect,
            "primary_color": forms.TextInput(
                attrs={
                    "type": "color",
                    "class": "form-control form-control-color",
                }
            ),
        }
