# Generated migration for draft/published status on DecisionItem

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_remove_chat_feature'),
    ]

    operations = [
        # Add status field with default 'published' (existing items are published)
        migrations.AddField(
            model_name='decisionitem',
            name='status',
            field=models.CharField(
                choices=[('draft', 'Draft'), ('published', 'Published')],
                default='published',
                max_length=20,
            ),
        ),
        # Add created_by field (nullable for existing items)
        migrations.AddField(
            model_name='decisionitem',
            name='created_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='created_items',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        # Add indexes for efficient filtering
        migrations.AddIndex(
            model_name='decisionitem',
            index=models.Index(fields=['status'], name='decision_it_status_idx'),
        ),
        migrations.AddIndex(
            model_name='decisionitem',
            index=models.Index(fields=['created_by'], name='decision_it_created_by_idx'),
        ),
        migrations.AddIndex(
            model_name='decisionitem',
            index=models.Index(fields=['decision', 'status'], name='decision_it_dec_status_idx'),
        ),
    ]
