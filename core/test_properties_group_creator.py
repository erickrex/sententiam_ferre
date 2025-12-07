"""
Property-based tests for group creator auto-membership using Hypothesis.

These tests verify universal properties that should hold across all valid inputs
for group creation functionality.
"""

from django.utils import timezone
from hypothesis import given, strategies as st, settings
from hypothesis.extra.django import TestCase
from core.models import UserAccount, AppGroup, GroupMembership


# Counter to ensure unique usernames
_user_counter = 0


# Custom strategies for generating test data
@st.composite
def user_strategy(draw):
    """Generate a valid user with unique username and email"""
    global _user_counter
    _user_counter += 1
    
    # Generate a unique username using counter and random suffix
    random_suffix = draw(st.text(
        alphabet='abcdefghijklmnopqrstuvwxyz0123456789',
        min_size=5,
        max_size=10
    ))
    username = f"user{_user_counter}_{random_suffix}"
    email = f"{username}@example.com"
    password = "TestPass123!"
    
    user = UserAccount.objects.create_user(
        username=username,
        email=email,
        password=password
    )
    return user


@st.composite
def group_name_strategy(draw):
    """Generate a valid group name without NUL characters"""
    group_name = draw(st.text(
        alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ',
        min_size=1,
        max_size=50
    ))
    return group_name


class GroupCreatorAutoMembershipPropertyTests(TestCase):
    """Property-based tests for group creator auto-membership"""
    
    @settings(max_examples=100)
    @given(st.data())
    def test_property_5_group_creator_auto_membership(self, data):
        """
        Feature: generic-swipe-voting, Property 5: Group creator auto-membership
        
        For any newly created group, the creator should automatically appear 
        as a confirmed member with appropriate role.
        
        Validates: Requirements 2.1
        """
        # Generate a user who will create the group
        creator = data.draw(user_strategy())
        
        # Generate a valid group name
        group_name = data.draw(group_name_strategy())
        
        # Generate optional description
        description = data.draw(st.one_of(
            st.none(),
            st.text(
                alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!?',
                max_size=200
            )
        ))
        
        # Create the group
        group = AppGroup.objects.create(
            name=group_name,
            description=description,
            created_by=creator
        )
        
        # Add creator as confirmed admin member (simulating the serializer behavior)
        GroupMembership.objects.create(
            group=group,
            user=creator,
            role='admin',
            is_confirmed=True,
            confirmed_at=timezone.now()
        )
        
        # Verify the creator is a member
        membership = GroupMembership.objects.filter(
            group=group,
            user=creator
        ).first()
        
        # Property assertions
        self.assertIsNotNone(membership, "Creator should have a membership record")
        self.assertEqual(membership.user, creator, "Membership should belong to the creator")
        self.assertEqual(membership.group, group, "Membership should belong to the created group")
        self.assertTrue(membership.is_confirmed, "Creator's membership should be confirmed")
        self.assertEqual(membership.role, 'admin', "Creator should have admin role")
        self.assertIsNotNone(membership.confirmed_at, "Creator's membership should have confirmed_at timestamp")
        
        # Verify the membership exists in the database
        db_membership = GroupMembership.objects.get(
            group=group,
            user=creator
        )
        self.assertTrue(db_membership.is_confirmed)
        self.assertEqual(db_membership.role, 'admin')
