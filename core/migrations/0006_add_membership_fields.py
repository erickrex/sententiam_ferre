# Generated migration for group invitation/request enhancement

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_fix_trigger_uuid'),
    ]

    operations = [
        # Add membership_type field
        migrations.AddField(
            model_name='groupmembership',
            name='membership_type',
            field=models.CharField(
                max_length=20,
                choices=[('invitation', 'Invitation'), ('request', 'Request')],
                default='invitation'
            ),
        ),
        # Add status field
        migrations.AddField(
            model_name='groupmembership',
            name='status',
            field=models.CharField(
                max_length=20,
                choices=[('pending', 'Pending'), ('confirmed', 'Confirmed'), ('rejected', 'Rejected')],
                default='pending'
            ),
        ),
        # Add rejected_at field
        migrations.AddField(
            model_name='groupmembership',
            name='rejected_at',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
