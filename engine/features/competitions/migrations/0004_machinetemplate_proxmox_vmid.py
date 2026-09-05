from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('competitions', '0003_seed_machine_templates'),
    ]
    operations = [
        migrations.AddField(
            model_name='machinetemplate',
            name='proxmox_vmid',
            field=models.PositiveIntegerField(
                blank=True, null=True,
                help_text='ProxMox template VMID (e.g. 9001 for tmpl-debian8)'
            ),
        ),
    ]
