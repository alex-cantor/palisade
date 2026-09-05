from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('injects', '0002_inject_competition'),
    ]

    operations = [
        migrations.AddField(
            model_name='inject',
            name='description',
            field=models.TextField(blank=True),
        ),
    ]
