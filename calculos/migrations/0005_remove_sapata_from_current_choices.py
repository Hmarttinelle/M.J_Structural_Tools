from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calculos', '0004_alter_historicocalculo_input_data_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicocalculo',
            name='elemento',
            field=models.CharField(
                choices=[('Viga', 'Viga'), ('Pilar', 'Pilar')],
                max_length=10,
            ),
        ),
    ]
