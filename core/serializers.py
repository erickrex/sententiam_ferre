from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from core.models import (
    UserAccount, AppGroup, GroupMembership, Decision, DecisionSharedGroup, 
    Taxonomy, Term, DecisionItem, CatalogItem, DecisionItemTerm, CatalogItemTerm,
    DecisionVote, DecisionSelection, Conversation, Message, Question, AnswerOption, UserAnswer
)


class UserAccountSerializer(serializers.ModelSerializer):
    """Serializer for UserAccount model"""
    
    class Meta:
        model = UserAccount
        fields = ['id', 'username', 'email', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration with password validation"""
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = UserAccount
        fields = ['username', 'email', 'password', 'password_confirm']
    
    def validate_email(self, value):
        """Validate email uniqueness"""
        if UserAccount.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def validate_username(self, value):
        """Validate username uniqueness"""
        if UserAccount.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value
    
    def validate(self, attrs):
        """Validate password complexity and matching"""
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')
        
        # Check if passwords match
        if password != password_confirm:
            raise serializers.ValidationError({
                'password_confirm': 'Passwords do not match.'
            })
        
        # Validate password complexity using Django's validators
        try:
            validate_password(password)
        except DjangoValidationError as e:
            raise serializers.ValidationError({
                'password': list(e.messages)
            })
        
        return attrs
    
    def create(self, validated_data):
        """Create user with hashed password"""
        # Remove password_confirm as it's not needed for user creation
        validated_data.pop('password_confirm')
        
        # Create user with hashed password
        user = UserAccount.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    username = serializers.CharField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )



class GroupMembershipSerializer(serializers.ModelSerializer):
    """Serializer for GroupMembership model"""
    user = UserAccountSerializer(read_only=True)
    user_id = serializers.UUIDField(write_only=True, required=False)
    group_name = serializers.CharField(source='group.name', read_only=True)
    
    class Meta:
        model = GroupMembership
        fields = [
            'id', 'group', 'group_name', 'user', 'user_id', 'role', 
            'membership_type', 'status', 'is_confirmed', 
            'invited_at', 'confirmed_at', 'rejected_at'
        ]
        read_only_fields = ['id', 'invited_at', 'confirmed_at', 'rejected_at']


class AppGroupSerializer(serializers.ModelSerializer):
    """Serializer for AppGroup model"""
    created_by = UserAccountSerializer(read_only=True)
    member_count = serializers.SerializerMethodField()
    
    class Meta:
        model = AppGroup
        fields = ['id', 'name', 'description', 'created_by', 'created_at', 'member_count']
        read_only_fields = ['id', 'created_by', 'created_at']
    
    def get_member_count(self, obj):
        """Get count of confirmed members"""
        return obj.memberships.filter(is_confirmed=True).count()
    
    def create(self, validated_data):
        """Create group and add creator as confirmed admin member"""
        user = self.context['request'].user
        
        # Create the group
        group = AppGroup.objects.create(
            created_by=user,
            **validated_data
        )
        
        # Add creator as confirmed admin member with proper fields
        GroupMembership.objects.create(
            group=group,
            user=user,
            role='admin',
            membership_type='invitation',  # Creator is treated as auto-accepted invitation
            status='confirmed',
            is_confirmed=True,
            confirmed_at=timezone.now()
        )
        
        return group


class AppGroupDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for AppGroup with members"""
    created_by = UserAccountSerializer(read_only=True)
    members = GroupMembershipSerializer(source='memberships', many=True, read_only=True)
    
    class Meta:
        model = AppGroup
        fields = ['id', 'name', 'description', 'created_by', 'created_at', 'members']
        read_only_fields = ['id', 'created_by', 'created_at']


class InviteUserSerializer(serializers.Serializer):
    """Serializer for inviting a user to a group"""
    user_id = serializers.UUIDField(required=False)
    username = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    role = serializers.ChoiceField(
        choices=['admin', 'member'],
        default='member'
    )
    
    def validate(self, attrs):
        """Validate that at least one identifier is provided"""
        if not any([attrs.get('user_id'), attrs.get('username'), attrs.get('email')]):
            raise serializers.ValidationError(
                "At least one of user_id, username, or email must be provided"
            )
        return attrs


class JoinRequestSerializer(serializers.Serializer):
    """Serializer for creating join requests"""
    group_name = serializers.CharField(required=True)
    
    def validate_group_name(self, value):
        """Validate group exists, user not member, no pending request"""
        # Get the user from context
        request = self.context.get('request')
        if not request or not request.user:
            raise serializers.ValidationError("User must be authenticated")
        
        user = request.user
        
        # Check if group exists
        try:
            group = AppGroup.objects.get(name=value)
        except AppGroup.DoesNotExist:
            raise serializers.ValidationError("Group not found")
        
        # Check if user is already a confirmed member
        if GroupMembership.objects.filter(
            group=group,
            user=user,
            status='confirmed'
        ).exists():
            raise serializers.ValidationError("You are already a member of this group")
        
        # Check if user has a pending request
        if GroupMembership.objects.filter(
            group=group,
            user=user,
            membership_type='request',
            status='pending'
        ).exists():
            raise serializers.ValidationError("You already have a pending request for this group")
        
        # Store the group in the serializer for later use
        self.group = group
        return value


class MembershipActionSerializer(serializers.Serializer):
    """Serializer for membership actions (accept, reject, approve, decline, resend, delete)"""
    action = serializers.ChoiceField(
        choices=['accept', 'reject', 'approve', 'decline', 'resend', 'delete'],
        required=True
    )



def validate_locked_params(locked_params):
    """
    Validate locked_params structure for Decision rules.
    
    Args:
        locked_params: The locked_params dict to validate
        
    Raises:
        serializers.ValidationError: If validation fails
    """
    if not isinstance(locked_params, dict):
        raise serializers.ValidationError("locked_params must be a JSON object")
    
    for param_name, param_value in locked_params.items():
        if param_name not in Decision.LOCKABLE_PARAMS:
            raise serializers.ValidationError(
                f"Invalid locked parameter: '{param_name}'. "
                f"Valid parameters: {', '.join(Decision.LOCKABLE_PARAMS)}"
            )
        
        valid_values = Decision.VALID_PARAM_VALUES.get(param_name, [])
        if param_value not in valid_values:
            raise serializers.ValidationError(
                f"Invalid value '{param_value}' for locked parameter '{param_name}'. "
                f"Valid values: {', '.join(valid_values)}"
            )


class DecisionSerializer(serializers.ModelSerializer):
    """Serializer for Decision model with rule validation"""
    group_name = serializers.CharField(source='group.name', read_only=True)
    locked_params = serializers.SerializerMethodField()
    
    class Meta:
        model = Decision
        fields = [
            'id', 'group', 'group_name', 'title', 'description', 
            'item_type', 'rules', 'status', 'created_at', 'updated_at',
            'locked_params'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'locked_params']
    
    def get_locked_params(self, obj):
        """Return the locked parameters from rules"""
        return obj.get_locked_params()
    
    def validate_rules(self, value):
        """Validate rules JSON structure including locked_params"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Rules must be a JSON object")
        
        rule_type = value.get('type')
        if rule_type not in ['unanimous', 'threshold']:
            raise serializers.ValidationError(
                "Rule type must be 'unanimous' or 'threshold'"
            )
        
        if rule_type == 'threshold':
            threshold_value = value.get('value')
            if threshold_value is None:
                raise serializers.ValidationError(
                    "Threshold rules must include a 'value' field"
                )
            if not isinstance(threshold_value, (int, float)):
                raise serializers.ValidationError(
                    "Threshold value must be a number"
                )
            if not (0 <= threshold_value <= 1):
                raise serializers.ValidationError(
                    "Threshold value must be between 0 and 1"
                )
        
        # Validate locked_params if present
        locked_params = value.get('locked_params')
        if locked_params is not None:
            validate_locked_params(locked_params)
        
        return value
    
    def validate_status(self, value):
        """Validate status transitions"""
        if self.instance:
            # This is an update
            if not self.instance.can_transition_to(value):
                valid_transitions = Decision.VALID_TRANSITIONS.get(self.instance.status, [])
                raise serializers.ValidationError(
                    f"Cannot transition from '{self.instance.status}' to '{value}'. "
                    f"Valid transitions: {', '.join(valid_transitions) if valid_transitions else 'none'}"
                )
        return value


class DecisionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating decisions"""
    
    class Meta:
        model = Decision
        fields = [
            'group', 'title', 'description', 
            'item_type', 'rules', 'status'
        ]
    
    def validate_rules(self, value):
        """Validate rules JSON structure including locked_params"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Rules must be a JSON object")
        
        rule_type = value.get('type')
        if rule_type not in ['unanimous', 'threshold']:
            raise serializers.ValidationError(
                "Rule type must be 'unanimous' or 'threshold'"
            )
        
        if rule_type == 'threshold':
            threshold_value = value.get('value')
            if threshold_value is None:
                raise serializers.ValidationError(
                    "Threshold rules must include a 'value' field"
                )
            if not isinstance(threshold_value, (int, float)):
                raise serializers.ValidationError(
                    "Threshold value must be a number"
                )
            if not (0 <= threshold_value <= 1):
                raise serializers.ValidationError(
                    "Threshold value must be between 0 and 1"
                )
        
        # Validate locked_params if present
        locked_params = value.get('locked_params')
        if locked_params is not None:
            validate_locked_params(locked_params)
        
        return value


class DecisionUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating decisions"""
    
    class Meta:
        model = Decision
        fields = ['title', 'description', 'rules', 'status']
    
    def validate_rules(self, value):
        """Validate rules JSON structure including locked_params"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Rules must be a JSON object")
        
        rule_type = value.get('type')
        if rule_type not in ['unanimous', 'threshold']:
            raise serializers.ValidationError(
                "Rule type must be 'unanimous' or 'threshold'"
            )
        
        if rule_type == 'threshold':
            threshold_value = value.get('value')
            if threshold_value is None:
                raise serializers.ValidationError(
                    "Threshold rules must include a 'value' field"
                )
            if not isinstance(threshold_value, (int, float)):
                raise serializers.ValidationError(
                    "Threshold value must be a number"
                )
            if not (0 <= threshold_value <= 1):
                raise serializers.ValidationError(
                    "Threshold value must be between 0 and 1"
                )
        
        # Validate locked_params if present
        locked_params = value.get('locked_params')
        if locked_params is not None:
            validate_locked_params(locked_params)
        
        return value
    
    def validate_status(self, value):
        """Validate status transitions"""
        if self.instance and value != self.instance.status:
            if not self.instance.can_transition_to(value):
                valid_transitions = Decision.VALID_TRANSITIONS.get(self.instance.status, [])
                raise serializers.ValidationError(
                    f"Cannot transition from '{self.instance.status}' to '{value}'. "
                    f"Valid transitions: {', '.join(valid_transitions) if valid_transitions else 'none'}"
                )
        return value


class DecisionSharedGroupSerializer(serializers.ModelSerializer):
    """Serializer for DecisionSharedGroup model"""
    group_name = serializers.CharField(source='group.name', read_only=True)
    decision_title = serializers.CharField(source='decision.title', read_only=True)
    
    class Meta:
        model = DecisionSharedGroup
        fields = ['id', 'decision', 'decision_title', 'group', 'group_name', 'shared_at']
        read_only_fields = ['id', 'shared_at']



class TermSerializer(serializers.ModelSerializer):
    """Serializer for Term model"""
    taxonomy_name = serializers.CharField(source='taxonomy.name', read_only=True)
    
    class Meta:
        model = Term
        fields = ['id', 'taxonomy', 'taxonomy_name', 'value', 'attributes']
        read_only_fields = ['id']
    
    def validate_attributes(self, value):
        """Validate attributes is a valid JSON object if provided"""
        if value is not None and not isinstance(value, dict):
            raise serializers.ValidationError("Attributes must be a JSON object")
        return value


class TaxonomySerializer(serializers.ModelSerializer):
    """Serializer for Taxonomy model"""
    term_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Taxonomy
        fields = ['id', 'name', 'description', 'term_count']
        read_only_fields = ['id']
    
    def get_term_count(self, obj):
        """Get count of terms in this taxonomy"""
        return obj.terms.count()
    
    def validate_name(self, value):
        """Validate taxonomy name uniqueness"""
        # Check if this is an update
        if self.instance:
            # Exclude current instance from uniqueness check
            if Taxonomy.objects.filter(name=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError("A taxonomy with this name already exists.")
        else:
            # For new taxonomies, check if name exists
            if Taxonomy.objects.filter(name=value).exists():
                raise serializers.ValidationError("A taxonomy with this name already exists.")
        return value


class TaxonomyDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for Taxonomy with terms"""
    terms = TermSerializer(many=True, read_only=True)
    
    class Meta:
        model = Taxonomy
        fields = ['id', 'name', 'description', 'terms']
        read_only_fields = ['id']



class CatalogItemSerializer(serializers.ModelSerializer):
    """Serializer for CatalogItem model"""
    
    class Meta:
        model = CatalogItem
        fields = ['id', 'label', 'attributes', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def validate_attributes(self, value):
        """Validate attributes is a valid JSON object if provided"""
        if value is not None and not isinstance(value, dict):
            raise serializers.ValidationError("Attributes must be a JSON object")
        return value


class DecisionItemTermSerializer(serializers.ModelSerializer):
    """Serializer for DecisionItemTerm model"""
    term_value = serializers.CharField(source='term.value', read_only=True)
    taxonomy_name = serializers.CharField(source='term.taxonomy.name', read_only=True)
    
    class Meta:
        model = DecisionItemTerm
        fields = ['id', 'item', 'term', 'term_value', 'taxonomy_name']
        read_only_fields = ['id']


class DecisionItemSerializer(serializers.ModelSerializer):
    """Serializer for DecisionItem model with nested attribute handling"""
    catalog_item_label = serializers.CharField(source='catalog_item.label', read_only=True)
    tags = DecisionItemTermSerializer(source='item_terms', many=True, read_only=True)
    
    class Meta:
        model = DecisionItem
        fields = [
            'id', 'decision', 'catalog_item', 'catalog_item_label', 
            'label', 'attributes', 'external_ref', 'created_at', 'tags'
        ]
        read_only_fields = ['id', 'created_at']
    
    def validate_attributes(self, value):
        """Validate attributes is a valid JSON object if provided"""
        if value is not None and not isinstance(value, dict):
            raise serializers.ValidationError("Attributes must be a JSON object")
        return value
    
    def validate(self, attrs):
        """Validate uniqueness of external_ref and label per decision"""
        decision = attrs.get('decision')
        external_ref = attrs.get('external_ref')
        label = attrs.get('label')
        
        # Check for duplicate items
        if decision and label:
            query = DecisionItem.objects.filter(
                decision=decision,
                label=label
            )
            
            if external_ref:
                query = query.filter(external_ref=external_ref)
            
            # Exclude current instance if updating
            if self.instance:
                query = query.exclude(id=self.instance.id)
            
            if query.exists():
                raise serializers.ValidationError(
                    "An item with this label and external_ref already exists in this decision"
                )
        
        return attrs


class DecisionItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating decision items"""
    
    class Meta:
        model = DecisionItem
        fields = ['decision', 'catalog_item', 'label', 'attributes', 'external_ref']
    
    def validate_attributes(self, value):
        """Validate attributes is a valid JSON object if provided"""
        if value is not None and not isinstance(value, dict):
            raise serializers.ValidationError("Attributes must be a JSON object")
        return value
    
    def validate(self, attrs):
        """Validate uniqueness of external_ref and label per decision"""
        decision = attrs.get('decision')
        external_ref = attrs.get('external_ref')
        label = attrs.get('label')
        
        # Check for duplicate items
        if decision and label:
            query = DecisionItem.objects.filter(
                decision=decision,
                label=label
            )
            
            if external_ref:
                query = query.filter(external_ref=external_ref)
            
            if query.exists():
                raise serializers.ValidationError(
                    "An item with this label and external_ref already exists in this decision"
                )
        
        return attrs


class DecisionItemUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating decision items"""
    
    class Meta:
        model = DecisionItem
        fields = ['label', 'attributes', 'external_ref']
    
    def validate_attributes(self, value):
        """Validate attributes is a valid JSON object if provided"""
        if value is not None and not isinstance(value, dict):
            raise serializers.ValidationError("Attributes must be a JSON object")
        return value



class DecisionVoteSerializer(serializers.ModelSerializer):
    """Serializer for DecisionVote model with validation"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    item_label = serializers.CharField(source='item.label', read_only=True)
    
    class Meta:
        model = DecisionVote
        fields = [
            'id', 'item', 'user', 'user_username', 'item_label',
            'is_like', 'rating', 'weight', 'note', 'voted_at'
        ]
        read_only_fields = ['id', 'user', 'voted_at']
    
    def validate(self, attrs):
        """Validate that at least one of is_like or rating is provided"""
        is_like = attrs.get('is_like')
        rating = attrs.get('rating')
        
        # For updates, check if either field is being set or already exists
        if self.instance:
            # If updating, check the combined state
            final_is_like = is_like if is_like is not None else self.instance.is_like
            final_rating = rating if rating is not None else self.instance.rating
            
            if final_is_like is None and final_rating is None:
                raise serializers.ValidationError(
                    "At least one of is_like or rating must be provided"
                )
        else:
            # For new votes, at least one must be provided
            if is_like is None and rating is None:
                raise serializers.ValidationError(
                    "At least one of is_like or rating must be provided"
                )
        
        return attrs


class VoteSummarySerializer(serializers.Serializer):
    """Serializer for vote summary statistics"""
    total_votes = serializers.IntegerField()
    likes = serializers.IntegerField()
    dislikes = serializers.IntegerField()
    average_rating = serializers.FloatField(allow_null=True)
    rating_count = serializers.IntegerField()


class DecisionSelectionSerializer(serializers.ModelSerializer):
    """Serializer for DecisionSelection (Favourites) with item details and snapshot"""
    item = DecisionItemSerializer(read_only=True)
    decision_title = serializers.CharField(source='decision.title', read_only=True)
    
    class Meta:
        model = DecisionSelection
        fields = ['id', 'decision', 'decision_title', 'item', 'selected_at', 'snapshot']
        read_only_fields = ['id', 'decision', 'item', 'selected_at', 'snapshot']



class ConversationSerializer(serializers.ModelSerializer):
    """Serializer for Conversation model"""
    decision_title = serializers.CharField(source='decision.title', read_only=True)
    message_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = ['id', 'decision', 'decision_title', 'created_at', 'message_count']
        read_only_fields = ['id', 'created_at']
    
    def get_message_count(self, obj):
        """Get count of messages in this conversation"""
        return obj.messages.count()


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for Message model"""
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    sender_id = serializers.UUIDField(source='sender.id', read_only=True)
    
    class Meta:
        model = Message
        fields = [
            'id', 'conversation', 'sender', 'sender_id', 'sender_username',
            'text', 'sent_at', 'is_read'
        ]
        read_only_fields = ['id', 'sender', 'sent_at']


class MessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating messages"""
    
    class Meta:
        model = Message
        fields = ['conversation', 'text']
    
    def validate_text(self, value):
        """Validate that message text is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("Message text cannot be empty")
        return value


class MessageUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating message read status"""
    
    class Meta:
        model = Message
        fields = ['is_read']


class AnswerOptionSerializer(serializers.ModelSerializer):
    """Serializer for AnswerOption model"""
    
    class Meta:
        model = AnswerOption
        fields = ['id', 'question', 'text', 'order_num']
        read_only_fields = ['id']


class QuestionSerializer(serializers.ModelSerializer):
    """Serializer for Question model"""
    answer_options = AnswerOptionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Question
        fields = ['id', 'text', 'scope', 'item_type', 'created_at', 'answer_options']
        read_only_fields = ['id', 'created_at']
    
    def validate(self, attrs):
        """Validate that item_type is provided when scope is 'item_type'"""
        scope = attrs.get('scope')
        item_type = attrs.get('item_type')
        
        if scope == 'item_type' and not item_type:
            raise serializers.ValidationError(
                "item_type must be provided when scope is 'item_type'"
            )
        
        return attrs


class UserAnswerSerializer(serializers.ModelSerializer):
    """Serializer for UserAnswer model"""
    question_text = serializers.CharField(source='question.text', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = UserAnswer
        fields = [
            'id', 'user', 'user_username', 'question', 'question_text',
            'decision', 'answer_option', 'answer_value', 'answered_at'
        ]
        read_only_fields = ['id', 'user', 'answered_at']
    
    def validate(self, attrs):
        """Validate that at least one of answer_option or answer_value is provided"""
        answer_option = attrs.get('answer_option')
        answer_value = attrs.get('answer_value')
        
        # For updates, check if either field is being set or already exists
        if self.instance:
            final_answer_option = answer_option if answer_option is not None else self.instance.answer_option
            final_answer_value = answer_value if answer_value is not None else self.instance.answer_value
            
            if final_answer_option is None and final_answer_value is None:
                raise serializers.ValidationError(
                    "At least one of answer_option or answer_value must be provided"
                )
        else:
            # For new answers, at least one must be provided
            if answer_option is None and answer_value is None:
                raise serializers.ValidationError(
                    "At least one of answer_option or answer_value must be provided"
                )
        
        return attrs


class UserAnswerCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating user answers"""
    
    class Meta:
        model = UserAnswer
        fields = ['question', 'decision', 'answer_option', 'answer_value']
    
    def validate(self, attrs):
        """Validate that at least one of answer_option or answer_value is provided"""
        answer_option = attrs.get('answer_option')
        answer_value = attrs.get('answer_value')
        
        if answer_option is None and answer_value is None:
            raise serializers.ValidationError(
                "At least one of answer_option or answer_value must be provided"
            )
        
        return attrs


# Import GenerationJob model for serializers
from core.models import GenerationJob


class GenerationRequestSerializer(serializers.Serializer):
    """Serializer for character generation requests"""
    
    # Valid options for generation parameters
    VALID_ART_STYLES = ['cartoon', 'pixel_art', 'flat_vector', 'hand_drawn']
    VALID_VIEW_ANGLES = ['side_profile', 'front_facing', 'three_quarter']
    VALID_POSES = ['idle', 'action', 'jumping', 'attacking', 'celebrating']
    VALID_EXPRESSIONS = ['neutral', 'happy', 'angry', 'surprised', 'determined']
    VALID_BACKGROUNDS = ['transparent', 'solid_color', 'simple_gradient']
    VALID_COLOR_PALETTES = ['vibrant', 'pastel', 'muted', 'monochrome']
    
    description = serializers.CharField(
        required=True,
        min_length=1,
        max_length=500,
        help_text="Character description (e.g., 'friendly robot sidekick')"
    )
    art_style = serializers.ChoiceField(
        choices=VALID_ART_STYLES,
        required=True,
        help_text="Art style for the character"
    )
    view_angle = serializers.ChoiceField(
        choices=VALID_VIEW_ANGLES,
        required=True,
        help_text="View angle for the character"
    )
    pose = serializers.ChoiceField(
        choices=VALID_POSES,
        required=False,
        default='idle',
        help_text="Character pose"
    )
    expression = serializers.ChoiceField(
        choices=VALID_EXPRESSIONS,
        required=False,
        default='neutral',
        help_text="Facial expression"
    )
    background = serializers.ChoiceField(
        choices=VALID_BACKGROUNDS,
        required=False,
        default='transparent',
        help_text="Background type"
    )
    color_palette = serializers.ChoiceField(
        choices=VALID_COLOR_PALETTES,
        required=False,
        default='vibrant',
        help_text="Color palette"
    )
    
    def validate_description(self, value):
        """Validate description is not empty or whitespace"""
        if not value or not value.strip():
            raise serializers.ValidationError("Description cannot be empty")
        return value.strip()


class GenerationJobSerializer(serializers.ModelSerializer):
    """Serializer for GenerationJob model"""
    item_label = serializers.CharField(source='item.label', read_only=True)
    item_id = serializers.UUIDField(source='item.id', read_only=True)
    decision_id = serializers.UUIDField(source='item.decision.id', read_only=True)
    decision_title = serializers.CharField(source='item.decision.title', read_only=True)
    
    class Meta:
        model = GenerationJob
        fields = [
            'id', 'item_id', 'item_label', 'decision_id', 'decision_title',
            'request_id', 'status', 'parameters', 'image_url', 
            'error_message', 'created_at', 'updated_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'request_id', 'status', 'image_url', 
            'error_message', 'created_at', 'updated_at', 'completed_at'
        ]


class GenerationStatusSerializer(serializers.Serializer):
    """Serializer for generation status response"""
    pending = serializers.IntegerField()
    processing = serializers.IntegerField()
    completed = serializers.IntegerField()
    failed = serializers.IntegerField()


class VariationRequestSerializer(serializers.Serializer):
    """
    Serializer for character variation requests.
    
    All fields are optional - if not provided, values will be inherited
    from the parent item.
    """
    
    # Valid options for generation parameters (same as GenerationRequestSerializer)
    VALID_ART_STYLES = ['cartoon', 'pixel_art', 'flat_vector', 'hand_drawn']
    VALID_VIEW_ANGLES = ['side_profile', 'front_facing', 'three_quarter']
    VALID_POSES = ['idle', 'action', 'jumping', 'attacking', 'celebrating']
    VALID_EXPRESSIONS = ['neutral', 'happy', 'angry', 'surprised', 'determined']
    VALID_BACKGROUNDS = ['transparent', 'solid_color', 'simple_gradient']
    VALID_COLOR_PALETTES = ['vibrant', 'pastel', 'muted', 'monochrome']
    
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500,
        help_text="Character description (optional - inherits from parent if not provided)"
    )
    art_style = serializers.ChoiceField(
        choices=VALID_ART_STYLES,
        required=False,
        allow_null=True,
        help_text="Art style for the character (optional)"
    )
    view_angle = serializers.ChoiceField(
        choices=VALID_VIEW_ANGLES,
        required=False,
        allow_null=True,
        help_text="View angle for the character (optional)"
    )
    pose = serializers.ChoiceField(
        choices=VALID_POSES,
        required=False,
        allow_null=True,
        help_text="Character pose (optional)"
    )
    expression = serializers.ChoiceField(
        choices=VALID_EXPRESSIONS,
        required=False,
        allow_null=True,
        help_text="Facial expression (optional)"
    )
    background = serializers.ChoiceField(
        choices=VALID_BACKGROUNDS,
        required=False,
        allow_null=True,
        help_text="Background type (optional)"
    )
    color_palette = serializers.ChoiceField(
        choices=VALID_COLOR_PALETTES,
        required=False,
        allow_null=True,
        help_text="Color palette (optional)"
    )
    
    def validate_description(self, value):
        """Validate description is not just whitespace if provided"""
        if value and not value.strip():
            return None  # Treat whitespace-only as not provided
        return value.strip() if value else None


class CharacterExportSerializer(serializers.Serializer):
    """
    Serializer for exporting character parameters as JSON.
    
    Includes all generation parameters, character description, and metadata.
    """
    id = serializers.UUIDField(read_only=True)
    description = serializers.CharField(read_only=True)
    generation_params = serializers.DictField(read_only=True)
    version = serializers.IntegerField(read_only=True)
    parent_item_id = serializers.CharField(read_only=True, allow_null=True)
    image_url = serializers.URLField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    creator = serializers.CharField(read_only=True, allow_null=True)
    decision_id = serializers.UUIDField(read_only=True)
    decision_title = serializers.CharField(read_only=True)
    
    @classmethod
    def from_decision_item(cls, item, creator_username=None):
        """
        Create export data from a DecisionItem.
        
        Args:
            item: DecisionItem instance
            creator_username: Optional username of the creator
        
        Returns:
            Dict with export data
        """
        attributes = item.attributes or {}
        
        return {
            'id': item.id,
            'description': attributes.get('description', item.label),
            'generation_params': attributes.get('generation_params', {}),
            'version': attributes.get('version', 1),
            'parent_item_id': attributes.get('parent_item_id'),
            'image_url': attributes.get('image_url'),
            'created_at': item.created_at,
            'creator': creator_username,
            'decision_id': item.decision_id,
            'decision_title': item.decision.title if item.decision else None,
        }
