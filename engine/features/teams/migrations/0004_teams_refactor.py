from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('teams', '0003_alter_team_competition'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Create TeamMember before dropping the user field so we don't lose data
        migrations.CreateModel(
            name='TeamMember',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='team_membership',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('team', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='members',
                    to='teams.team',
                )),
            ],
        ),
        # Migrate existing Team.user → TeamMember rows
        migrations.RunSQL(
            sql="""
                INSERT INTO teams_teammember (user_id, team_id)
                SELECT user_id, id FROM teams_team
                WHERE user_id IS NOT NULL
                ON CONFLICT DO NOTHING;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        # Drop the user column from Team
        migrations.RemoveField(
            model_name='team',
            name='user',
        ),
    ]
