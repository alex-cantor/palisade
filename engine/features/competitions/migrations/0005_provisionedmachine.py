import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('competitions', '0004_machinetemplate_proxmox_vmid'),
        ('teams', '0003_alter_team_competition'),
    ]
    operations = [
        migrations.CreateModel(
            name='ProvisionedMachine',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('vmid', models.PositiveIntegerField(unique=True)),
                ('name', models.CharField(max_length=100)),
                ('status', models.CharField(
                    choices=[('pending','Pending'),('running','Running'),('stopped','Stopped'),('error','Error')],
                    default='pending', max_length=20
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('competition', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='provisioned_machines', to='competitions.competition')),
                ('machine_template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='competitions.machinetemplate')),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='vms', to='teams.team')),
            ],
        ),
    ]
