# Migration to add indexes for new membership fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_migrate_existing_membership_data'),
    ]

    operations = [
        # Add index for (group, status)
        migrations.AddIndex(
            model_name='groupmembership',
            index=models.Index(fields=['group', 'status'], name='core_groupm_group_i_status_idx'),
        ),
        # Add index for (user, status)
        migrations.AddIndex(
            model_name='groupmembership',
            index=models.Index(fields=['user', 'status'], name='core_groupm_user_id_status_idx'),
        ),
        # Add index for (membership_type, status)
        migrations.AddIndex(
            model_name='groupmembership',
            index=models.Index(fields=['membership_type', 'status'], name='core_groupm_members_status_idx'),
        ),
    ]
