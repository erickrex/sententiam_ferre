"""
Property-based tests for GroupMembership model constraints using Hypothesis.

These tests verify universal properties that should hold across all valid inputs
for group membership functionality.
"""

from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone
from hypothesis import given, strategies as st, settings
from hypothesis.extra.django import TestCase
from rest_framework.test import APIRequestFactory
from core.models import UserAccount, AppGroup, GroupMembership
from core.serializers import JoinRequestSerializer


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
    
    # Generate a valid group name without NUL characters and ensure it's not blank
    group_name = draw(st.text(
        alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-',
        min_size=1,
        max_size=50
    ))
    
    # Ensure the group name is not just whitespace
    if not group_name.strip():
        group_name = f"TestGroup{_user_counter}"
    
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
        membership_type='invitation',
        status='confirmed',
        is_confirmed=True,
        confirmed_at=timezone.now()
    )
    
    return group, admin


class GroupMembershipPropertyTests(TestCase):
    """Property-based tests for GroupMembership model"""
    
    @settings(max_examples=100)
    @given(st.data())
    def test_property_8_unique_membership_constraint(self, data):
        """
        Feature: group-invitation-requests, Property 8: Unique membership constraint
        
        For any group and user combination, only one GroupMembership record 
        should exist at any time.
        
        Validates: Requirements 10.1, 10.7
        """
        # Generate a group with admin
        group, admin = data.draw(group_with_admin_strategy())
        
        # Generate a user
        user = data.draw(user_strategy())
        
        # Ensure no existing membership
        GroupMembership.objects.filter(group=group, user=user).delete()
        
        # Generate random membership data
        role = data.draw(st.sampled_from(['admin', 'member']))
        membership_type = data.draw(st.sampled_from(['invitation', 'request']))
        status = data.draw(st.sampled_from(['pending', 'confirmed', 'rejected']))
        
        # Create first membership
        membership1 = GroupMembership.objects.create(
            group=group,
            user=user,
            role=role,
            membership_type=membership_type,
            status=status,
            is_confirmed=(status == 'confirmed')
        )
        
        # Verify first membership was created
        self.assertIsNotNone(membership1)
        self.assertEqual(
            GroupMembership.objects.filter(group=group, user=user).count(),
            1
        )
        
        # Attempt to create a second membership with same group and user
        # This should raise an IntegrityError due to unique_together constraint
        # Use atomic block to handle the transaction properly
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                GroupMembership.objects.create(
                    group=group,
                    user=user,
                    role=data.draw(st.sampled_from(['admin', 'member'])),
                    membership_type=data.draw(st.sampled_from(['invitation', 'request'])),
                    status=data.draw(st.sampled_from(['pending', 'confirmed', 'rejected'])),
                    is_confirmed=False
                )
        
        # Verify only one membership still exists
        self.assertEqual(
            GroupMembership.objects.filter(group=group, user=user).count(),
            1
        )
        
        # Verify the original membership is unchanged
        membership1.refresh_from_db()
        self.assertEqual(membership1.group, group)
        self.assertEqual(membership1.user, user)
        self.assertEqual(membership1.role, role)
        self.assertEqual(membership1.membership_type, membership_type)
        self.assertEqual(membership1.status, status)
    
    @settings(max_examples=100)
    @given(st.data())
    def test_property_12_validation_prevents_invalid_users(self, data):
        """
        Feature: group-invitation-requests, Property 12: Validation prevents invalid users
        
        For any invitation or join request, attempting to use a non-existent 
        user or group should be rejected with appropriate error message.
        
        Validates: Requirements 2.3, 6.4
        """
        # Generate a user for the request
        user = data.draw(user_strategy())
        
        # Generate a random non-existent group name
        invalid_group_name = data.draw(st.text(
            alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
            min_size=10,
            max_size=50
        ))
        
        # Ensure this group name doesn't exist
        while AppGroup.objects.filter(name=invalid_group_name).exists():
            invalid_group_name = invalid_group_name + "_unique"
        
        # Create a mock request with the user
        factory = APIRequestFactory()
        request = factory.post('/fake-url/')
        request.user = user
        
        # Try to validate with non-existent group
        serializer = JoinRequestSerializer(
            data={'group_name': invalid_group_name},
            context={'request': request}
        )
        
        # Validation should fail
        self.assertFalse(serializer.is_valid())
        
        # Should have error for group_name field
        self.assertIn('group_name', serializer.errors)
        
        # Error message should indicate group not found
        error_message = str(serializer.errors['group_name'][0])
        self.assertEqual(error_message, "Group not found")
    
    @settings(max_examples=100)
    @given(st.data())
    def test_property_13_validation_prevents_duplicate_members(self, data):
        """
        Feature: group-invitation-requests, Property 13: Validation prevents duplicate members
        
        For any invitation or join request, attempting to add a user who is 
        already a confirmed member should be rejected.
        
        Validates: Requirements 2.4, 6.5
        """
        # Generate a group with admin
        group, admin = data.draw(group_with_admin_strategy())
        
        # Generate a user and make them a confirmed member
        user = data.draw(user_strategy())
        
        # Create confirmed membership
        GroupMembership.objects.create(
            group=group,
            user=user,
            role='member',
            membership_type='invitation',
            status='confirmed',
            is_confirmed=True,
            confirmed_at=timezone.now()
        )
        
        # Create a mock request with the user
        factory = APIRequestFactory()
        request = factory.post('/fake-url/')
        request.user = user
        
        # Try to create a join request for a group they're already in
        serializer = JoinRequestSerializer(
            data={'group_name': group.name},
            context={'request': request}
        )
        
        # Validation should fail
        self.assertFalse(serializer.is_valid())
        
        # Should have error for group_name field
        self.assertIn('group_name', serializer.errors)
        
        # Error message should indicate already a member
        error_message = str(serializer.errors['group_name'][0])
        self.assertEqual(error_message, "You are already a member of this group")

    @settings(max_examples=100)
    @given(st.data())
    def test_property_1_join_request_creation(self, data):
        """
        Feature: group-invitation-requests, Property 1: Join request creation
        
        For any user and valid group name, creating a join request should result 
        in a GroupMembership record with membership_type='request' and status='pending'.
        
        Validates: Requirements 2.2
        """
        # Generate a group with admin
        group, admin = data.draw(group_with_admin_strategy())
        
        # Generate a user (not a member)
        user = data.draw(user_strategy())
        
        # Ensure no existing membership
        GroupMembership.objects.filter(group=group, user=user).delete()
        
        # Create a mock request with the user
        factory = APIRequestFactory()
        request = factory.post('/fake-url/')
        request.user = user
        
        # Validate the join request
        serializer = JoinRequestSerializer(
            data={'group_name': group.name},
            context={'request': request}
        )
        
        # Validation should succeed
        self.assertTrue(serializer.is_valid(), f"Validation failed: {serializer.errors}")
        
        # Create the join request
        membership = GroupMembership.objects.create(
            group=serializer.group,
            user=user,
            role='member',
            membership_type='request',
            status='pending',
            is_confirmed=False
        )
        
        # Verify the membership was created with correct attributes
        self.assertIsNotNone(membership)
        self.assertEqual(membership.group, group)
        self.assertEqual(membership.user, user)
        self.assertEqual(membership.membership_type, 'request')
        self.assertEqual(membership.status, 'pending')
        self.assertFalse(membership.is_confirmed)
        self.assertIsNone(membership.confirmed_at)
        self.assertIsNone(membership.rejected_at)
    
    @settings(max_examples=100)
    @given(st.data())
    def test_property_2_duplicate_request_prevention(self, data):
        """
        Feature: group-invitation-requests, Property 2: Duplicate request prevention
        
        For any user and group combination, attempting to create a join request 
        when a pending request already exists should be rejected.
        
        Validates: Requirements 2.5, 10.6
        """
        # Generate a group with admin
        group, admin = data.draw(group_with_admin_strategy())
        
        # Generate a user
        user = data.draw(user_strategy())
        
        # Ensure no existing membership
        GroupMembership.objects.filter(group=group, user=user).delete()
        
        # Create an existing PENDING join request
        existing_membership = GroupMembership.objects.create(
            group=group,
            user=user,
            role='member',
            membership_type='request',
            status='pending',
            is_confirmed=False
        )
        
        # Verify the existing membership was created
        self.assertIsNotNone(existing_membership)
        
        # Create a mock request with the user
        factory = APIRequestFactory()
        request = factory.post('/fake-url/')
        request.user = user
        
        # Try to create another join request
        serializer = JoinRequestSerializer(
            data={'group_name': group.name},
            context={'request': request}
        )
        
        # Validation should fail for pending requests
        self.assertFalse(serializer.is_valid())
        self.assertIn('group_name', serializer.errors)
        error_message = str(serializer.errors['group_name'][0])
        self.assertEqual(error_message, "You already have a pending request for this group")
        
        # Verify only one membership exists
        membership_count = GroupMembership.objects.filter(
            group=group,
            user=user
        ).count()
        self.assertEqual(membership_count, 1)

    @settings(max_examples=100)
    @given(st.data())
    def test_property_9_user_request_visibility(self, data):
        """
        Feature: group-invitation-requests, Property 9: User request visibility
        
        For any user, querying their join requests should return only memberships 
        where user matches and membership_type='request'.
        
        Validates: Requirements 3.1
        """
        # Generate a user
        user = data.draw(user_strategy())
        
        # Generate multiple groups
        num_groups = data.draw(st.integers(min_value=1, max_value=5))
        groups_and_admins = [data.draw(group_with_admin_strategy()) for _ in range(num_groups)]
        
        # Create various memberships for this user
        request_memberships = []
        invitation_memberships = []
        
        for i, (group, admin) in enumerate(groups_and_admins):
            # Ensure no existing membership
            GroupMembership.objects.filter(group=group, user=user).delete()
            
            # Randomly decide what type of membership to create
            membership_type = data.draw(st.sampled_from(['request', 'invitation']))
            status = data.draw(st.sampled_from(['pending', 'rejected']))
            
            membership = GroupMembership.objects.create(
                group=group,
                user=user,
                role='member',
                membership_type=membership_type,
                status=status,
                is_confirmed=False,
                rejected_at=timezone.now() if status == 'rejected' else None
            )
            
            if membership_type == 'request':
                request_memberships.append(membership)
            else:
                invitation_memberships.append(membership)
        
        # Query for user's join requests
        user_requests = GroupMembership.objects.filter(
            user=user,
            membership_type='request'
        ).filter(
            Q(status='pending') | Q(status='rejected')
        )
        
        # Verify that only request-type memberships are returned
        self.assertEqual(user_requests.count(), len(request_memberships))
        
        # Verify each returned membership is a request
        for membership in user_requests:
            self.assertEqual(membership.user, user)
            self.assertEqual(membership.membership_type, 'request')
            self.assertIn(membership.status, ['pending', 'rejected'])
        
        # Verify invitations are not included
        for invitation in invitation_memberships:
            self.assertNotIn(invitation, list(user_requests))

    @settings(max_examples=100)
    @given(st.data())
    def test_property_6_resend_updates_status(self, data):
        """
        Feature: group-invitation-requests, Property 6: Resend updates status
        
        For any rejected membership, resending should update status='pending', 
        update invited_at, and clear rejected_at.
        
        Validates: Requirements 4.2, 8.3
        """
        # Generate a group with admin
        group, admin = data.draw(group_with_admin_strategy())
        
        # Generate a user
        user = data.draw(user_strategy())
        
        # Ensure no existing membership
        GroupMembership.objects.filter(group=group, user=user).delete()
        
        # Create a rejected join request
        rejected_time = timezone.now()
        membership = GroupMembership.objects.create(
            group=group,
            user=user,
            role='member',
            membership_type='request',
            status='rejected',
            is_confirmed=False,
            rejected_at=rejected_time
        )
        
        # Store the original invited_at time
        original_invited_at = membership.invited_at
        
        # Verify initial state
        self.assertEqual(membership.status, 'rejected')
        self.assertIsNotNone(membership.rejected_at)
        
        # Resend the request
        membership.status = 'pending'
        membership.invited_at = timezone.now()
        membership.rejected_at = None
        membership.save()
        
        # Refresh from database
        membership.refresh_from_db()
        
        # Verify the status was updated
        self.assertEqual(membership.status, 'pending')
        
        # Verify invited_at was updated (should be later than original)
        self.assertGreater(membership.invited_at, original_invited_at)
        
        # Verify rejected_at was cleared
        self.assertIsNone(membership.rejected_at)
        
        # Verify other fields remain unchanged
        self.assertEqual(membership.group, group)
        self.assertEqual(membership.user, user)
        self.assertEqual(membership.membership_type, 'request')
        self.assertFalse(membership.is_confirmed)
    
    @settings(max_examples=100)
    @given(st.data())
    def test_property_7_delete_removes_record(self, data):
        """
        Feature: group-invitation-requests, Property 7: Delete removes record
        
        For any rejected membership, deleting should permanently remove the 
        GroupMembership record from the database.
        
        Validates: Requirements 4.3, 8.4, 9.3
        """
        # Generate a group with admin
        group, admin = data.draw(group_with_admin_strategy())
        
        # Generate a user
        user = data.draw(user_strategy())
        
        # Ensure no existing membership
        GroupMembership.objects.filter(group=group, user=user).delete()
        
        # Create a rejected membership (can be either request or invitation)
        membership_type = data.draw(st.sampled_from(['request', 'invitation']))
        
        membership = GroupMembership.objects.create(
            group=group,
            user=user,
            role='member',
            membership_type=membership_type,
            status='rejected',
            is_confirmed=False,
            rejected_at=timezone.now()
        )
        
        # Store the membership ID
        membership_id = membership.id
        
        # Verify the membership exists
        self.assertTrue(
            GroupMembership.objects.filter(id=membership_id).exists()
        )
        
        # Delete the membership
        membership.delete()
        
        # Verify the membership no longer exists
        self.assertFalse(
            GroupMembership.objects.filter(id=membership_id).exists()
        )
        
        # Verify no membership exists for this user and group
        self.assertEqual(
            GroupMembership.objects.filter(group=group, user=user).count(),
            0
        )

    @settings(max_examples=100)
    @given(st.data())
    def test_property_10_user_invitation_visibility(self, data):
        """
        Feature: group-invitation-requests, Property 10: User invitation visibility
        
        For any user, querying their invitations should return only memberships 
        where user matches and membership_type='invitation'.
        
        Validates: Requirements 5.1
        """
        # Generate a user
        user = data.draw(user_strategy())
        
        # Generate multiple groups
        num_groups = data.draw(st.integers(min_value=1, max_value=5))
        groups_and_admins = [data.draw(group_with_admin_strategy()) for _ in range(num_groups)]
        
        # Create various memberships for this user
        invitation_memberships = []
        request_memberships = []
        
        for i, (group, admin) in enumerate(groups_and_admins):
            # Ensure no existing membership
            GroupMembership.objects.filter(group=group, user=user).delete()
            
            # Randomly decide what type of membership to create
            membership_type = data.draw(st.sampled_from(['request', 'invitation']))
            status = data.draw(st.sampled_from(['pending', 'rejected']))
            
            membership = GroupMembership.objects.create(
                group=group,
                user=user,
                role='member',
                membership_type=membership_type,
                status=status,
                is_confirmed=False,
                rejected_at=timezone.now() if status == 'rejected' else None
            )
            
            if membership_type == 'invitation':
                invitation_memberships.append(membership)
            else:
                request_memberships.append(membership)
        
        # Query for user's invitations
        user_invitations = GroupMembership.objects.filter(
            user=user,
            membership_type='invitation'
        ).filter(
            Q(status='pending') | Q(status='rejected')
        )
        
        # Verify that only invitation-type memberships are returned
        self.assertEqual(user_invitations.count(), len(invitation_memberships))
        
        # Verify each returned membership is an invitation
        for membership in user_invitations:
            self.assertEqual(membership.user, user)
            self.assertEqual(membership.membership_type, 'invitation')
            self.assertIn(membership.status, ['pending', 'rejected'])
        
        # Verify requests are not included
        for request in request_memberships:
            self.assertNotIn(request, list(user_invitations))

    @settings(max_examples=100)
    @given(st.data())
    def test_property_4_status_transition_to_confirmed(self, data):
        """
        Feature: group-invitation-requests, Property 4: Status transition to confirmed
        
        For any pending membership (invitation or request), accepting/approving it 
        should update status='confirmed' and set confirmed_at timestamp.
        
        Validates: Requirements 5.3, 7.3, 10.4
        """
        # Generate a group with admin
        group, admin = data.draw(group_with_admin_strategy())
        
        # Generate a user
        user = data.draw(user_strategy())
        
        # Ensure no existing membership
        GroupMembership.objects.filter(group=group, user=user).delete()
        
        # Create a pending membership (can be either invitation or request)
        membership_type = data.draw(st.sampled_from(['invitation', 'request']))
        
        membership = GroupMembership.objects.create(
            group=group,
            user=user,
            role='member',
            membership_type=membership_type,
            status='pending',
            is_confirmed=False
        )
        
        # Verify initial state
        self.assertEqual(membership.status, 'pending')
        self.assertFalse(membership.is_confirmed)
        self.assertIsNone(membership.confirmed_at)
        
        # Accept/approve the membership
        membership.status = 'confirmed'
        membership.is_confirmed = True
        membership.confirmed_at = timezone.now()
        membership.save()
        
        # Refresh from database
        membership.refresh_from_db()
        
        # Verify the status was updated to confirmed
        self.assertEqual(membership.status, 'confirmed')
        self.assertTrue(membership.is_confirmed)
        
        # Verify confirmed_at was set
        self.assertIsNotNone(membership.confirmed_at)
        
        # Verify confirmed_at is a recent timestamp (within last minute)
        time_diff = timezone.now() - membership.confirmed_at
        self.assertLess(time_diff.total_seconds(), 60)
        
        # Verify other fields remain unchanged
        self.assertEqual(membership.group, group)
        self.assertEqual(membership.user, user)
        self.assertEqual(membership.membership_type, membership_type)
        self.assertIsNone(membership.rejected_at)

    @settings(max_examples=100)
    @given(st.data())
    def test_property_5_status_transition_to_rejected(self, data):
        """
        Feature: group-invitation-requests, Property 5: Status transition to rejected
        
        For any pending membership, rejecting/declining it should update 
        status='rejected' and set rejected_at timestamp.
        
        Validates: Requirements 5.4, 7.4, 10.5
        """
        # Generate a group with admin
        group, admin = data.draw(group_with_admin_strategy())
        
        # Generate a user
        user = data.draw(user_strategy())
        
        # Ensure no existing membership
        GroupMembership.objects.filter(group=group, user=user).delete()
        
        # Create a pending membership (can be either invitation or request)
        membership_type = data.draw(st.sampled_from(['invitation', 'request']))
        
        membership = GroupMembership.objects.create(
            group=group,
            user=user,
            role='member',
            membership_type=membership_type,
            status='pending',
            is_confirmed=False
        )
        
        # Verify initial state
        self.assertEqual(membership.status, 'pending')
        self.assertFalse(membership.is_confirmed)
        self.assertIsNone(membership.rejected_at)
        
        # Reject/decline the membership
        membership.status = 'rejected'
        membership.rejected_at = timezone.now()
        membership.save()
        
        # Refresh from database
        membership.refresh_from_db()
        
        # Verify the status was updated to rejected
        self.assertEqual(membership.status, 'rejected')
        self.assertFalse(membership.is_confirmed)
        
        # Verify rejected_at was set
        self.assertIsNotNone(membership.rejected_at)
        
        # Verify rejected_at is a recent timestamp (within last minute)
        time_diff = timezone.now() - membership.rejected_at
        self.assertLess(time_diff.total_seconds(), 60)
        
        # Verify other fields remain unchanged
        self.assertEqual(membership.group, group)
        self.assertEqual(membership.user, user)
        self.assertEqual(membership.membership_type, membership_type)
        self.assertIsNone(membership.confirmed_at)

    @settings(max_examples=100)
    @given(st.data())
    def test_property_3_invitation_creation_with_type(self, data):
        """
        Feature: group-invitation-requests, Property 3: Invitation creation with type
        
        For any admin invitation, the created GroupMembership should have 
        membership_type='invitation' and status='pending'.
        
        Validates: Requirements 6.3
        """
        # Generate a group with admin
        group, admin = data.draw(group_with_admin_strategy())
        
        # Generate a user to invite
        user_to_invite = data.draw(user_strategy())
        
        # Ensure no existing membership
        GroupMembership.objects.filter(group=group, user=user_to_invite).delete()
        
        # Generate random role
        role = data.draw(st.sampled_from(['admin', 'member']))
        
        # Create an invitation (simulating what the endpoint does)
        membership = GroupMembership.objects.create(
            group=group,
            user=user_to_invite,
            role=role,
            membership_type='invitation',
            status='pending',
            is_confirmed=False
        )
        
        # Verify the membership was created with correct attributes
        self.assertIsNotNone(membership)
        self.assertEqual(membership.group, group)
        self.assertEqual(membership.user, user_to_invite)
        self.assertEqual(membership.role, role)
        self.assertEqual(membership.membership_type, 'invitation')
        self.assertEqual(membership.status, 'pending')
        self.assertFalse(membership.is_confirmed)
        self.assertIsNone(membership.confirmed_at)
        self.assertIsNone(membership.rejected_at)
        
        # Verify the invitation is queryable as an invitation
        invitations = GroupMembership.objects.filter(
            user=user_to_invite,
            membership_type='invitation',
            status='pending'
        )
        self.assertEqual(invitations.count(), 1)
        self.assertEqual(invitations.first(), membership)

    @settings(max_examples=100)
    @given(st.data())
    def test_property_11_admin_request_visibility(self, data):
        """
        Feature: group-invitation-requests, Property 11: Admin request visibility
        
        For any group admin, querying join requests should return only memberships 
        where group matches, membership_type='request', and status='pending'.
        
        Validates: Requirements 7.1
        """
        # Generate a group with admin
        group, admin = data.draw(group_with_admin_strategy())
        
        # Generate multiple users and create various memberships
        num_users = data.draw(st.integers(min_value=2, max_value=6))
        
        pending_requests = []
        other_memberships = []
        
        for i in range(num_users):
            user = data.draw(user_strategy())
            
            # Ensure no existing membership
            GroupMembership.objects.filter(group=group, user=user).delete()
            
            # Randomly decide what type of membership to create
            membership_type = data.draw(st.sampled_from(['request', 'invitation']))
            status = data.draw(st.sampled_from(['pending', 'rejected', 'confirmed']))
            
            membership = GroupMembership.objects.create(
                group=group,
                user=user,
                role='member',
                membership_type=membership_type,
                status=status,
                is_confirmed=(status == 'confirmed'),
                confirmed_at=timezone.now() if status == 'confirmed' else None,
                rejected_at=timezone.now() if status == 'rejected' else None
            )
            
            # Track which memberships should be visible to admin
            if membership_type == 'request' and status == 'pending':
                pending_requests.append(membership)
            else:
                other_memberships.append(membership)
        
        # Query for pending join requests (what the endpoint does)
        admin_visible_requests = GroupMembership.objects.filter(
            group=group,
            membership_type='request',
            status='pending'
        )
        
        # Verify that only pending requests are returned
        self.assertEqual(admin_visible_requests.count(), len(pending_requests))
        
        # Verify each returned membership is a pending request
        for membership in admin_visible_requests:
            self.assertEqual(membership.group, group)
            self.assertEqual(membership.membership_type, 'request')
            self.assertEqual(membership.status, 'pending')
        
        # Verify other memberships are not included
        for membership in other_memberships:
            self.assertNotIn(membership, list(admin_visible_requests))
        
        # Verify all pending requests are included
        for membership in pending_requests:
            self.assertIn(membership, list(admin_visible_requests))
