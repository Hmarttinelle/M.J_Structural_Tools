# Generated for M.J. Structural Tools v1.2
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("calculos", "0005_remove_sapata_from_current_choices"),
    ]

    operations = [
        migrations.AddField(
            model_name="systemconfiguration",
            name="sidebar_image",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to="sidebar/",
                verbose_name="Imagem da Barra Lateral",
            ),
        ),
    ]
