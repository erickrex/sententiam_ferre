import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator


class UserAccount(AbstractUser):
    """Custom user model extending Django's AbstractUser"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_account'

    def __str__(self):
        return self.username


class AppGroup(models.Model):
    """Group entity for collaborative decision-making"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        UserAccount,
        on_delete=models.CASCADE,
        related_name='created_groups'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'app_group'

    def __str__(self):
        return self.name


class GroupMembership(models.Model):
    """Links users to groups with role and confirmation status"""
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('member', 'Member'),
    ]
    
    MEMBERSHIP_TYPE_CHOICES = [
        ('invitation', 'Invitation'),  # Admin invited user
        ('request', 'Request'),        # User requested to join
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('rejected', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(
        AppGroup,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    user = models.ForeignKey(
        UserAccount,
        on_delete=models.CASCADE,
        related_name='group_memberships'
    )
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='member')
    membership_type = models.CharField(
        max_length=20,
        choices=MEMBERSHIP_TYPE_CHOICES,
        default='invitation'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    is_confirmed = models.BooleanField(default=False)
    invited_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'group_membership'
        unique_together = [['group', 'user']]
        indexes = [
            models.Index(fields=['group', 'is_confirmed']),
            models.Index(fields=['group', 'status']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['membership_type', 'status']),
        ]

    def __str__(self):
        return f"{self.user.username} in {self.group.name}"


class Decision(models.Model):
    """Decision entity with approval rules and status"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('archived', 'Archived'),
    ]

    # Valid status transitions
    VALID_TRANSITIONS = {
        'draft': ['open', 'archived'],
        'open': ['closed', 'archived'],
        'closed': ['archived'],
        'archived': []
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(
        AppGroup,
        on_delete=models.CASCADE,
        related_name='decisions'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    item_type = models.CharField(max_length=100, blank=True, null=True)
    rules = models.JSONField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'decision'
        indexes = [
            models.Index(fields=['group']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return self.title
    
    def can_transition_to(self, new_status):
        """Check if transition to new_status is valid"""
        return new_status in self.VALID_TRANSITIONS.get(self.status, [])
    
    # Valid parameter names that can be locked for 2D character generation
    LOCKABLE_PARAMS = [
        'art_style',
        'view_angle', 
        'color_palette',
        'pose',
        'expression',
        'background',
    ]
    
    # Valid values for each lockable parameter
    VALID_PARAM_VALUES = {
        'art_style': ['cartoon', 'pixel_art', 'flat_vector', 'hand_drawn'],
        'view_angle': ['side_profile', 'front_facing', 'three_quarter'],
        'color_palette': ['vibrant', 'pastel', 'muted', 'monochrome'],
        'pose': ['idle', 'action', 'jumping', 'attacking', 'celebrating'],
        'expression': ['neutral', 'happy', 'angry', 'surprised', 'determined'],
        'background': ['transparent', 'solid_color', 'simple_gradient'],
    }
    
    def validate_rules(self):
        """Validate the rules JSON structure including locked_params"""
        if not isinstance(self.rules, dict):
            raise ValueError("Rules must be a JSON object")
        
        rule_type = self.rules.get('type')
        if rule_type not in ['unanimous', 'threshold']:
            raise ValueError("Rule type must be 'unanimous' or 'threshold'")
        
        if rule_type == 'threshold':
            value = self.rules.get('value')
            if value is None:
                raise ValueError("Threshold rules must include a 'value' field")
            if not isinstance(value, (int, float)):
                raise ValueError("Threshold value must be a number")
            if not (0 <= value <= 1):
                raise ValueError("Threshold value must be between 0 and 1")
        
        # Validate locked_params if present
        locked_params = self.rules.get('locked_params')
        if locked_params is not None:
            if not isinstance(locked_params, dict):
                raise ValueError("locked_params must be a JSON object")
            
            for param_name, param_value in locked_params.items():
                if param_name not in self.LOCKABLE_PARAMS:
                    raise ValueError(
                        f"Invalid locked parameter: '{param_name}'. "
                        f"Valid parameters: {', '.join(self.LOCKABLE_PARAMS)}"
                    )
                
                valid_values = self.VALID_PARAM_VALUES.get(param_name, [])
                if param_value not in valid_values:
                    raise ValueError(
                        f"Invalid value '{param_value}' for locked parameter '{param_name}'. "
                        f"Valid values: {', '.join(valid_values)}"
                    )
        
        return True
    
    def get_locked_params(self):
        """Get the locked parameters for this decision"""
        if not self.rules:
            return {}
        return self.rules.get('locked_params', {})
    
    def is_param_locked(self, param_name):
        """Check if a specific parameter is locked"""
        locked_params = self.get_locked_params()
        return param_name in locked_params
    
    def get_locked_param_value(self, param_name):
        """Get the locked value for a parameter, or None if not locked"""
        locked_params = self.get_locked_params()
        return locked_params.get(param_name)


class DecisionSharedGroup(models.Model):
    """Many-to-many for cross-group decisions"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    decision = models.ForeignKey(
        Decision,
        on_delete=models.CASCADE,
        related_name='shared_groups'
    )
    group = models.ForeignKey(
        AppGroup,
        on_delete=models.CASCADE,
        related_name='shared_decisions'
    )
    shared_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'decision_shared_group'
        unique_together = [['decision', 'group']]
        indexes = [
            models.Index(fields=['decision']),
            models.Index(fields=['group']),
        ]

    def __str__(self):
        return f"{self.decision.title} shared with {self.group.name}"


class CatalogItem(models.Model):
    """Reusable item templates"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    label = models.CharField(max_length=255)
    attributes = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'catalog_item'

    def __str__(self):
        return self.label


class DecisionItem(models.Model):
    """Item within a decision that users can vote on"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    decision = models.ForeignKey(
        Decision,
        on_delete=models.CASCADE,
        related_name='items'
    )
    catalog_item = models.ForeignKey(
        CatalogItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='decision_items'
    )
    label = models.CharField(max_length=255)
    attributes = models.JSONField(null=True, blank=True)
    external_ref = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'decision_item'
        unique_together = [['decision', 'external_ref', 'label']]
        indexes = [
            models.Index(fields=['decision']),
            models.Index(fields=['catalog_item']),
        ]

    def __str__(self):
        return self.label
    
    # Character versioning helper methods
    
    def get_parent_item_id(self):
        """Get the parent item ID from attributes, if any."""
        if not self.attributes:
            return None
        return self.attributes.get('parent_item_id')
    
    def get_parent_item(self):
        """Get the parent DecisionItem, if any."""
        parent_id = self.get_parent_item_id()
        if not parent_id:
            return None
        try:
            return DecisionItem.objects.get(id=parent_id)
        except DecisionItem.DoesNotExist:
            return None
    
    def get_version(self):
        """Get the version number from attributes."""
        if not self.attributes:
            return 1
        return self.attributes.get('version', 1)
    
    def set_parent_item(self, parent_item):
        """
        Set the parent item reference and calculate version number.
        
        Args:
            parent_item: The parent DecisionItem instance.
        """
        if self.attributes is None:
            self.attributes = {}
        
        self.attributes['parent_item_id'] = str(parent_item.id)
        
        # Calculate version: parent's version + 1
        parent_version = parent_item.get_version()
        self.attributes['version'] = parent_version + 1
    
    def get_child_items(self):
        """
        Get all direct child items (variations) of this item.
        
        Returns:
            QuerySet of DecisionItem instances that have this item as parent.
        """
        # We need to filter by attributes JSON field
        # This requires a database that supports JSON queries (PostgreSQL)
        return DecisionItem.objects.filter(
            decision=self.decision,
            attributes__parent_item_id=str(self.id)
        )
    
    def get_variation_count(self):
        """Get the count of direct child variations."""
        return self.get_child_items().count()
    
    def get_version_chain(self):
        """
        Get the complete version chain from root to this item.
        
        Returns:
            List of DecisionItem instances from root ancestor to this item.
        """
        chain = [self]
        current = self
        
        # Walk up the parent chain
        while True:
            parent = current.get_parent_item()
            if parent is None:
                break
            chain.insert(0, parent)
            current = parent
        
        return chain
    
    def get_root_item(self):
        """
        Get the root item in the version chain.
        
        Returns:
            The root DecisionItem (the one with no parent).
        """
        chain = self.get_version_chain()
        return chain[0] if chain else self
    
    def get_generation_params(self):
        """Get the generation parameters from attributes."""
        if not self.attributes:
            return {}
        return self.attributes.get('generation_params', {})
    
    def get_param_diff_from_parent(self):
        """
        Get the parameters that differ from the parent item.
        
        Returns:
            Dict of parameter names to (parent_value, current_value) tuples.
            Empty dict if no parent or no differences.
        """
        parent = self.get_parent_item()
        if not parent:
            return {}
        
        parent_params = parent.get_generation_params()
        current_params = self.get_generation_params()
        
        diff = {}
        all_keys = set(parent_params.keys()) | set(current_params.keys())
        
        for key in all_keys:
            parent_val = parent_params.get(key)
            current_val = current_params.get(key)
            if parent_val != current_val:
                diff[key] = (parent_val, current_val)
        
        return diff
    
    def is_character_item(self):
        """Check if this item is a 2D character item."""
        if not self.attributes:
            return False
        return self.attributes.get('type') == '2d_character'


class DecisionVote(models.Model):
    """User vote on an item"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    item = models.ForeignKey(
        DecisionItem,
        on_delete=models.CASCADE,
        related_name='votes'
    )
    user = models.ForeignKey(
        UserAccount,
        on_delete=models.CASCADE,
        related_name='votes'
    )
    is_like = models.BooleanField(null=True, blank=True)
    rating = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    weight = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    note = models.TextField(null=True, blank=True)
    voted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'decision_vote'
        unique_together = [['user', 'item']]
        indexes = [
            models.Index(fields=['item']),
            models.Index(fields=['user']),
        ]
        constraints = [
            models.CheckConstraint(
                check=~models.Q(is_like__isnull=True, rating__isnull=True),
                name='vote_requires_is_like_or_rating'
            )
        ]

    def __str__(self):
        return f"{self.user.username} vote on {self.item.label}"
    
    def clean(self):
        """Validate that at least one of is_like or rating is provided"""
        from django.core.exceptions import ValidationError
        if self.is_like is None and self.rating is None:
            raise ValidationError("At least one of is_like or rating must be provided")


class DecisionSelection(models.Model):
    """Items that met approval rules (Favourites)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    decision = models.ForeignKey(
        Decision,
        on_delete=models.CASCADE,
        related_name='selections'
    )
    item = models.ForeignKey(
        DecisionItem,
        on_delete=models.CASCADE,
        related_name='selections'
    )
    selected_at = models.DateTimeField(auto_now_add=True)
    snapshot = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'decision_selection'
        unique_together = [['decision', 'item']]
        indexes = [
            models.Index(fields=['decision']),
            models.Index(fields=['item']),
        ]

    def __str__(self):
        return f"{self.item.label} selected in {self.decision.title}"


class Conversation(models.Model):
    """Chat thread associated with a decision"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    decision = models.OneToOneField(
        Decision,
        on_delete=models.CASCADE,
        related_name='conversation'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'conversation'

    def __str__(self):
        return f"Conversation for {self.decision.title}"


class Message(models.Model):
    """Individual message in a conversation"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        UserAccount,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    text = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        db_table = 'message'
        indexes = [
            models.Index(fields=['conversation', 'sent_at']),
            models.Index(fields=['sender']),
        ]
        ordering = ['sent_at']

    def __str__(self):
        return f"Message from {self.sender.username} at {self.sent_at}"


class Taxonomy(models.Model):
    """Classification system for organizing items"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'taxonomy'
        verbose_name_plural = 'taxonomies'

    def __str__(self):
        return self.name


class Term(models.Model):
    """Specific value within a taxonomy"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    taxonomy = models.ForeignKey(
        Taxonomy,
        on_delete=models.CASCADE,
        related_name='terms'
    )
    value = models.CharField(max_length=255)
    attributes = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'term'
        unique_together = [['taxonomy', 'value']]
        indexes = [
            models.Index(fields=['taxonomy']),
        ]

    def __str__(self):
        return f"{self.taxonomy.name}: {self.value}"


class DecisionItemTerm(models.Model):
    """Links items to taxonomy terms (tagging)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    item = models.ForeignKey(
        DecisionItem,
        on_delete=models.CASCADE,
        related_name='item_terms'
    )
    term = models.ForeignKey(
        Term,
        on_delete=models.CASCADE,
        related_name='item_terms'
    )

    class Meta:
        db_table = 'decision_item_term'
        unique_together = [['item', 'term']]
        indexes = [
            models.Index(fields=['item']),
            models.Index(fields=['term']),
        ]

    def __str__(self):
        return f"{self.item.label} tagged with {self.term.value}"


class CatalogItemTerm(models.Model):
    """Links catalog items to taxonomy terms"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    catalog_item = models.ForeignKey(
        CatalogItem,
        on_delete=models.CASCADE,
        related_name='catalog_terms'
    )
    term = models.ForeignKey(
        Term,
        on_delete=models.CASCADE,
        related_name='catalog_terms'
    )

    class Meta:
        db_table = 'catalog_item_term'
        unique_together = [['catalog_item', 'term']]
        indexes = [
            models.Index(fields=['catalog_item']),
            models.Index(fields=['term']),
        ]

    def __str__(self):
        return f"{self.catalog_item.label} tagged with {self.term.value}"


class Question(models.Model):
    """Question for capturing user preferences"""
    SCOPE_CHOICES = [
        ('global', 'Global'),
        ('item_type', 'Item Type'),
        ('decision', 'Decision'),
        ('group', 'Group'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    text = models.TextField()
    scope = models.CharField(max_length=50, choices=SCOPE_CHOICES)
    item_type = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'question'
        indexes = [
            models.Index(fields=['scope']),
        ]

    def __str__(self):
        return self.text[:50]


class AnswerOption(models.Model):
    """Predefined answer choices for questions"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='answer_options'
    )
    text = models.CharField(max_length=255)
    order_num = models.IntegerField()

    class Meta:
        db_table = 'answer_option'
        indexes = [
            models.Index(fields=['question']),
        ]
        ordering = ['order_num']

    def __str__(self):
        return self.text


class UserAnswer(models.Model):
    """User responses to questions"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        UserAccount,
        on_delete=models.CASCADE,
        related_name='answers'
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='user_answers'
    )
    decision = models.ForeignKey(
        Decision,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='user_answers'
    )
    answer_option = models.ForeignKey(
        AnswerOption,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user_answers'
    )
    answer_value = models.JSONField(null=True, blank=True)
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_answer'
        unique_together = [['user', 'question', 'decision']]
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['question']),
            models.Index(fields=['decision']),
        ]

    def __str__(self):
        return f"{self.user.username} answer to {self.question.text[:30]}"


class GenerationJob(models.Model):
    """Tracks the status of BRIA API generation requests for character images"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    item = models.ForeignKey(
        DecisionItem,
        on_delete=models.CASCADE,
        related_name='generation_jobs'
    )
    request_id = models.CharField(max_length=255, null=True, blank=True)  # BRIA request_id
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    parameters = models.JSONField()  # Generation parameters sent to BRIA
    image_url = models.URLField(max_length=2048, null=True, blank=True)  # Final image URL
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'generation_job'
        indexes = [
            models.Index(fields=['item']),
            models.Index(fields=['status']),
            models.Index(fields=['request_id']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"GenerationJob {self.id} for {self.item.label} ({self.status})"
