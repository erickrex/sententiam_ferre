"""
Property-based tests for invitation flow using Hypothesis.

These tests verify universal properties that should hold across all valid inputs
for group invitation functionality.
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
def group_with_admin_strategy(draw):
    """Generate a group with an admin user"""
    global _user_counter
    _user_counter += 1
    
    admin = draw(user_strategy())
    
    # Generate a valid group name without NUL characters
    group_name = draw(st.text(
        alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ',
        min_size=1,
        max_size=50
    ))
    
    group = AppGroup.objects.create(
        name=group_name,
        description="Test group",
        created_by=admin
    )
    
    # Create admin membership
    GroupMembership.objects.create(
        group=group,
        user=admin,
        role='admin',
        is_confirmed=True,
        confirmed_at=timezone.now()
    )
    
    return group, admin


class InvitationFlowPropertyTests(TestCase):
    """Property-based tests for invitation flow"""
    
    @settings(max_examples=100)
    @given(st.data())
    def test_property_6_invitation_creates_pending_membership(self, data):
        """
        Feature: generic-swipe-voting, Property 6: Invitation creates pending membership
        
        For any registered user invited to a group, a group_membership record 
        with is_confirmed=FALSE should be created.
        
        Validates: Requirements 2.2
        """
        # Generate a group with admin
        group, admin = data.draw(group_with_admin_strategy())
        
        # Generate a user to invite
        invitee = data.draw(user_strategy())
        
        # Ensure invitee is not already a member
        GroupMembership.objects.filter(group=group, user=invitee).delete()
        
        # Create invitation
        role = data.draw(st.sampled_from(['admin', 'member']))
        invitation = GroupMembership.objects.create(
            group=group,
            user=invitee,
            role=role,
            is_confirmed=False
        )
        
        # Verify invitation was created with correct properties
        self.assertIsNotNone(invitation)
        self.assertEqual(invitation.group, group)
        self.assertEqual(invitation.user, invitee)
        self.assertEqual(invitation.role, role)
        self.assertFalse(invitation.is_confirmed)
        self.assertIsNotNone(invitation.invited_at)
        self.assertIsNone(invitation.confirmed_at)
        
        # Verify the invitation exists in database
        db_invitation = GroupMembership.objects.get(
            group=group,
            user=invitee
        )
        self.assertFalse(db_invitation.is_confirmed)
    
    @settings(max_examples=100)
    @given(st.data())
    def test_property_7_invitation_acceptance_updates_status(self, data):
        """
        Feature: generic-swipe-voting, Property 7: Invitation acceptance updates status
        
        For any pending invitation, accepting it should set is_confirmed=TRUE 
        and preserve all other membership data.
        
        Validates: Requirements 2.4
        """
        # Generate a group with admin
        group, admin = data.draw(group_with_admin_strategy())
        
        # Generate a user to invite
        invitee = data.draw(user_strategy())
        
        # Ensure invitee is not already a member
        GroupMembership.objects.filter(group=group, user=invitee).delete()
        
        # Create pending invitation
        role = data.draw(st.sampled_from(['admin', 'member']))
        invitation = GroupMembership.objects.create(
            group=group,
            user=invitee,
            role=role,
            is_confirmed=False
        )
        
        # Store original values
        original_id = invitation.id
        original_group = invitation.group
        original_user = invitation.user
        original_role = invitation.role
        original_invited_at = invitation.invited_at
        
        # Accept invitation
        invitation.is_confirmed = True
        invitation.confirmed_at = timezone.now()
        invitation.save()
        
        # Refresh from database
        invitation.refresh_from_db()
        
        # Verify status was updated
        self.assertTrue(invitation.is_confirmed)
        self.assertIsNotNone(invitation.confirmed_at)
        
        # Verify all other data was preserved
        self.assertEqual(invitation.id, original_id)
        self.assertEqual(invitation.group, original_group)
        self.assertEqual(invitation.user, original_user)
        self.assertEqual(invitation.role, original_role)
        self.assertEqual(invitation.invited_at, original_invited_at)
    
    @settings(max_examples=100)
    @given(st.data())
    def test_property_8_invitation_decline_removes_membership(self, data):
        """
        Feature: generic-swipe-voting, Property 8: Invitation decline removes membership
        
        For any pending invitation, declining it should remove the 
        group_membership record entirely.
        
        Validates: Requirements 2.5
        """
        # Generate a group with admin
        group, admin = data.draw(group_with_admin_strategy())
        
        # Generate a user to invite
        invitee = data.draw(user_strategy())
        
        # Ensure invitee is not already a member
        GroupMembership.objects.filter(group=group, user=invitee).delete()
        
        # Create pending invitation
        role = data.draw(st.sampled_from(['admin', 'member']))
        invitation = GroupMembership.objects.create(
            group=group,
            user=invitee,
            role=role,
            is_confirmed=False
        )
        
        # Store invitation ID for verification
        invitation_id = invitation.id
        
        # Verify invitation exists
        self.assertTrue(
            GroupMembership.objects.filter(
                group=group,
                user=invitee
            ).exists()
        )
        
        # Decline invitation (delete the membership)
        invitation.delete()
        
        # Verify invitation was removed
        self.assertFalse(
            GroupMembership.objects.filter(
                group=group,
                user=invitee
            ).exists()
        )
        
        # Verify by ID as well
        self.assertFalse(
            GroupMembership.objects.filter(id=invitation_id).exists()
        )
