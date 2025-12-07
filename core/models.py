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
    
    def validate_rules(self):
        """Validate the rules JSON structure"""
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
        
        return True


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
