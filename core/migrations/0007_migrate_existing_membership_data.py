# Migration to update existing GroupMembership records with new field values

from django.db import migrations


def migrate_existing_data(apps, schema_editor):
    """
    Set all existing records to membership_type='invitation'
    Set status='confirmed' where is_confirmed=TRUE
    Set status='pending' where is_confirmed=FALSE
    """
    GroupMembership = apps.get_model('core', 'GroupMembership')
    
    # Update confirmed memberships
    GroupMembership.objects.filter(is_confirmed=True).update(
        membership_type='invitation',
        status='confirmed'
    )
    
    # Update pending memberships
    GroupMembership.objects.filter(is_confirmed=False).update(
        membership_type='invitation',
        status='pending'
    )


def reverse_migration(apps, schema_editor):
    """
    Reverse the migration by resetting to default values
    """
    GroupMembership = apps.get_model('core', 'GroupMembership')
    
    # Reset all to defaults
    GroupMembership.objects.all().update(
        membership_type='invitation',
        status='pending'
    )


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_add_membership_fields'),
    ]

    operations = [
        migrations.RunPython(migrate_existing_data, reverse_migration),
    ]
