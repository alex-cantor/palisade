from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('announcements', '0002_announcement_competition'),
    ]

    operations = [
        migrations.AddField(
            model_name='announcement',
            name='scheduled_for',
            field=models.DateTimeField(blank=True, help_text="Leave blank to publish immediately. If set, competitors won't see this until that time.", null=True),
        ),
        migrations.AlterField(
            model_name='announcement',
            name='read',
            field=models.BooleanField(default=False),
        ),
    ]
