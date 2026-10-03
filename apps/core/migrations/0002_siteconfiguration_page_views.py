from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="siteconfiguration",
            name="page_views",
            field=models.PositiveBigIntegerField(default=0, verbose_name="Visites du site"),
        ),
    ]
