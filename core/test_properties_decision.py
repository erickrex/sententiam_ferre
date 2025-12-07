"""
Property-based tests for Decision module

These tests use Hypothesis to verify correctness properties across all valid inputs.
Each test runs a minimum of 100 iterations with randomly generated data.
"""

from hypothesis import given, strategies as st, settings
from hypothesis.extra.django import TestCase
from django.utils import timezone
from django.db import models
from core.models import UserAccount, AppGroup, GroupMembership, Decision


# Hypothesis strategies for generating test data
def safe_text(min_size=0, max_size=100):
    """Generate text without NUL characters or other problematic chars"""
    return st.text(
        alphabet=st.characters(
            blacklist_characters='\x00',
            blacklist_categories=('Cs', 'Cc')
        ),
        min_size=min_size,
        max_size=max_size
    )


@st.composite
def user_strategy(draw):
    """Generate a valid user"""
    import uuid as uuid_lib
    
    # Add UUID to ensure uniqueness
    unique_id = str(uuid_lib.uuid4())[:8]
    username = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), min_codepoint=65),
        min_size=3,
        max_size=12
    ))
    username = f"{username}_{unique_id}"
    email = f"{username.lower()}@example.com"
    password = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), min_codepoint=65),
        min_size=8,
        max_size=20
    ))
    
    user = UserAccount.objects.create_user(
        username=username,
        email=email,
        password=password
    )
    return user


@st.composite
def group_strategy(draw, user=None):
    """Generate a valid group"""
    if user is None:
        user = draw(user_strategy())
    
    name = draw(safe_text(min_size=1, max_size=100))
    description = draw(safe_text(min_size=0, max_size=500))
    
    group = AppGroup.objects.create(
        name=name,
        description=description,
        created_by=user
    )
    
    # Add creator as confirmed admin
    GroupMembership.objects.create(
        group=group,
        user=user,
        role='admin',
        is_confirmed=True,
        confirmed_at=timezone.now()
    )
    
    return group


@st.composite
def unanimous_rules_strategy(draw):
    """Generate unanimous approval rules"""
    return {'type': 'unanimous'}


@st.composite
def threshold_rules_strategy(draw):
    """Generate threshold approval rules with valid value"""
    value = draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))
    return {'type': 'threshold', 'value': value}


@st.composite
def rules_strategy(draw):
    """Generate either unanimous or threshold rules"""
    return draw(st.one_of(unanimous_rules_strategy(), threshold_rules_strategy()))


@st.composite
def decision_data_strategy(draw, group=None):
    """Generate valid decision data"""
    if group is None:
        user = draw(user_strategy())
        group = draw(group_strategy(user=user))
    
    title = draw(safe_text(min_size=1, max_size=200))
    description = draw(safe_text(min_size=0, max_size=1000))
    item_type = draw(safe_text(min_size=0, max_size=50))
    rules = draw(rules_strategy())
    status = draw(st.sampled_from(['draft', 'open', 'closed', 'archived']))
    
    return {
        'group': group,
        'title': title,
        'description': description,
        'item_type': item_type,
        'rules': rules,
        'status': status
    }


class DecisionPropertyTests(TestCase):
    """Property-based tests for Decision creation and management"""
    
    @settings(max_examples=100, deadline=None)
    @given(decision_data=decision_data_strategy())
    def test_property_9_decision_field_persistence(self, decision_data):
        """
        Feature: generic-swipe-voting, Property 9: Decision field persistence
        
        For any decision creation, all provided fields (title, description, 
        item_type, rules, status) should be retrievable unchanged.
        
        Validates: Requirements 3.1
        """
        # Create decision with all fields
        decision = Decision.objects.create(**decision_data)
        
        # Retrieve the decision
        retrieved = Decision.objects.get(id=decision.id)
        
        # Verify all fields are preserved
        assert retrieved.title == decision_data['title']
        assert retrieved.description == decision_data['description']
        assert retrieved.item_type == decision_data['item_type']
        assert retrieved.rules == decision_data['rules']
        assert retrieved.status == decision_data['status']
        assert retrieved.group == decision_data['group']
    
    @settings(max_examples=100, deadline=None)
    @given(
        threshold_value=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        user=user_strategy(),
    )
    def test_property_10_threshold_rule_validation(self, threshold_value, user):
        """
        Feature: generic-swipe-voting, Property 10: Threshold rule validation
        
        For any threshold value between 0 and 1, creating a decision with that 
        threshold should store the rules JSON correctly with type "threshold" 
        and the specified value.
        
        Validates: Requirements 3.3
        """
        # Create group
        group = AppGroup.objects.create(
            name="Test Group",
            description="Test",
            created_by=user
        )
        GroupMembership.objects.create(
            group=group,
            user=user,
            role='admin',
            is_confirmed=True,
            confirmed_at=timezone.now()
        )
        
        # Create decision with threshold rules
        rules = {'type': 'threshold', 'value': threshold_value}
        decision = Decision.objects.create(
            group=group,
            title="Test Decision",
            description="Test",
            rules=rules,
            status='open'
        )
        
        # Retrieve and verify
        retrieved = Decision.objects.get(id=decision.id)
        assert retrieved.rules['type'] == 'threshold'
        assert retrieved.rules['value'] == threshold_value
        
        # Verify validation passes
        assert retrieved.validate_rules() is True
    
    @settings(max_examples=100, deadline=None)
    @given(user=user_strategy())
    def test_property_11_decision_initial_status(self, user):
        """
        Feature: generic-swipe-voting, Property 11: Decision initial status
        
        For any newly created decision without explicit status, the initial 
        status should be "open".
        
        Validates: Requirements 3.4
        """
        # Create group
        group = AppGroup.objects.create(
            name="Test Group",
            description="Test",
            created_by=user
        )
        GroupMembership.objects.create(
            group=group,
            user=user,
            role='admin',
            is_confirmed=True,
            confirmed_at=timezone.now()
        )
        
        # Create decision without explicit status
        decision = Decision.objects.create(
            group=group,
            title="Test Decision",
            description="Test",
            rules={'type': 'unanimous'}
        )
        
        # Verify default status is 'open'
        assert decision.status == 'open'
        
        # Verify it persists
        retrieved = Decision.objects.get(id=decision.id)
        assert retrieved.status == 'open'
    
    @settings(max_examples=100, deadline=None)
    @given(
        from_status=st.sampled_from(['draft', 'open', 'closed']),
        user=user_strategy()
    )
    def test_property_12_decision_status_transitions(self, from_status, user):
        """
        Feature: generic-swipe-voting, Property 12: Decision status transitions
        
        For any decision status update, only valid state transitions 
        (draft→open, open→closed, closed→archived) should be allowed.
        
        Validates: Requirements 3.5
        """
        # Create group
        group = AppGroup.objects.create(
            name="Test Group",
            description="Test",
            created_by=user
        )
        GroupMembership.objects.create(
            group=group,
            user=user,
            role='admin',
            is_confirmed=True,
            confirmed_at=timezone.now()
        )
        
        # Create decision with initial status
        decision = Decision.objects.create(
            group=group,
            title="Test Decision",
            description="Test",
            rules={'type': 'unanimous'},
            status=from_status
        )
        
        # Get valid transitions for this status
        valid_transitions = Decision.VALID_TRANSITIONS[from_status]
        
        # Test all valid transitions
        for to_status in valid_transitions:
            assert decision.can_transition_to(to_status) is True
        
        # Test invalid transitions
        all_statuses = ['draft', 'open', 'closed', 'archived']
        invalid_transitions = [s for s in all_statuses if s not in valid_transitions and s != from_status]
        
        for to_status in invalid_transitions:
            assert decision.can_transition_to(to_status) is False



class DecisionSharingPropertyTests(TestCase):
    """Property-based tests for Decision sharing"""
    
    @settings(max_examples=100, deadline=None)
    @given(
        user1=user_strategy(),
        user2=user_strategy()
    )
    def test_property_47_decision_sharing_creates_link(self, user1, user2):
        """
        Feature: generic-swipe-voting, Property 47: Decision sharing creates link
        
        For any decision shared with another group, a decision_shared_group 
        record should be created linking the decision to the target group.
        
        Validates: Requirements 15.1
        """
        from core.models import DecisionSharedGroup
        
        # Create two groups
        group1 = AppGroup.objects.create(
            name="Group 1",
            description="Test",
            created_by=user1
        )
        GroupMembership.objects.create(
            group=group1,
            user=user1,
            role='admin',
            is_confirmed=True,
            confirmed_at=timezone.now()
        )
        
        group2 = AppGroup.objects.create(
            name="Group 2",
            description="Test",
            created_by=user2
        )
        GroupMembership.objects.create(
            group=group2,
            user=user2,
            role='admin',
            is_confirmed=True,
            confirmed_at=timezone.now()
        )
        
        # Create decision in group1
        decision = Decision.objects.create(
            group=group1,
            title="Test Decision",
            description="Test",
            rules={'type': 'unanimous'},
            status='open'
        )
        
        # Share with group2
        shared = DecisionSharedGroup.objects.create(
            decision=decision,
            group=group2
        )
        
        # Verify link was created
        assert DecisionSharedGroup.objects.filter(
            decision=decision,
            group=group2
        ).exists()
        
        # Verify the link is retrievable
        retrieved = DecisionSharedGroup.objects.get(id=shared.id)
        assert retrieved.decision == decision
        assert retrieved.group == group2
    
    @settings(max_examples=100, deadline=None)
    @given(
        user1=user_strategy(),
        user2=user_strategy()
    )
    def test_property_49_shared_group_access_permissions(self, user1, user2):
        """
        Feature: generic-swipe-voting, Property 49: Shared group access permissions
        
        For any user in a shared group, they should be able to view and vote 
        on the shared decision.
        
        Validates: Requirements 15.3
        """
        from core.models import DecisionSharedGroup
        
        # Create two groups
        group1 = AppGroup.objects.create(
            name="Group 1",
            description="Test",
            created_by=user1
        )
        GroupMembership.objects.create(
            group=group1,
            user=user1,
            role='admin',
            is_confirmed=True,
            confirmed_at=timezone.now()
        )
        
        group2 = AppGroup.objects.create(
            name="Group 2",
            description="Test",
            created_by=user2
        )
        GroupMembership.objects.create(
            group=group2,
            user=user2,
            role='admin',
            is_confirmed=True,
            confirmed_at=timezone.now()
        )
        
        # Create decision in group1
        decision = Decision.objects.create(
            group=group1,
            title="Test Decision",
            description="Test",
            rules={'type': 'unanimous'},
            status='open'
        )
        
        # Share with group2
        DecisionSharedGroup.objects.create(
            decision=decision,
            group=group2
        )
        
        # Verify user2 (member of group2) can access the decision
        # This is tested by checking if the decision appears in a query
        # that filters for decisions accessible to user2
        accessible_decisions = Decision.objects.filter(
            models.Q(
                group__memberships__user=user2,
                group__memberships__is_confirmed=True
            ) | models.Q(
                shared_groups__group__memberships__user=user2,
                shared_groups__group__memberships__is_confirmed=True
            )
        ).distinct()
        
        assert decision in accessible_decisions
        
        # Verify user1 (member of owning group) can still access
        accessible_to_user1 = Decision.objects.filter(
            models.Q(
                group__memberships__user=user1,
                group__memberships__is_confirmed=True
            ) | models.Q(
                shared_groups__group__memberships__user=user1,
                shared_groups__group__memberships__is_confirmed=True
            )
        ).distinct()
        
        assert decision in accessible_to_user1
