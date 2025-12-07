"""
Integration tests for join request and invitation flows.

Tests complete end-to-end workflows for the group invitation-requests feature.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from core.models import AppGroup, GroupMembership
from django.utils import timezone

User = get_user_model()


class JoinRequestIntegrationTests(TestCase):
    """Integration tests for complete join request and invitation workflows"""

    def setUp(self):
        """Set up test clients and users"""
        from rest_framework.authtoken.models import Token
        
        self.admin_client = APIClient()
        self.user_client = APIClient()
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='AdminPass123!'
        )
        
        # Create regular user
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@test.com',
            password='UserPass123!'
        )
        
        # Create tokens and authenticate clients
        admin_token, _ = Token.objects.get_or_create(user=self.admin_user)
        user_token, _ = Token.objects.get_or_create(user=self.regular_user)
        
        self.admin_client.credentials(HTTP_AUTHORIZATION=f'Token {admin_token.key}')
        self.user_client.credentials(HTTP_AUTHORIZATION=f'Token {user_token.key}')
        
        # Create a group
        self.group = AppGroup.objects.create(
            name='Test Group',
            description='A test group',
            created_by=self.admin_user
        )
        
        # Make admin user an admin member
        GroupMembership.objects.create(
            group=self.group,
            user=self.admin_user,
            role='admin',
            membership_type='invitation',
            status='confirmed',
            is_confirmed=True,
            confirmed_at=timezone.now()
        )

    def test_complete_join_request_flow(self):
        """
        Test complete user join request flow:
        1. User requests to join group
        2. Admin approves request
        3. User becomes confirmed member
        
        Requirements: All
        """
        # Step 1: User requests to join group
        join_request_data = {'group_name': 'Test Group'}
        response = self.user_client.post(
            '/api/v1/groups/join-request/',
            join_request_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        
        # Verify join request was created
        membership = GroupMembership.objects.get(
            group=self.group,
            user=self.regular_user
        )
        self.assertEqual(membership.membership_type, 'request')
        self.assertEqual(membership.status, 'pending')
        self.assertIsNone(membership.confirmed_at)
        self.assertIsNone(membership.rejected_at)
        
        # Step 2: Admin views pending join requests
        response = self.admin_client.get(
            f'/api/v1/groups/{self.group.id}/join-requests/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        requests = response.data['data']['results']
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0]['user']['username'], 'regular')
        self.assertEqual(requests[0]['status'], 'pending')
        
        # Step 3: Admin approves the request
        response = self.admin_client.patch(
            f'/api/v1/groups/{self.group.id}/join-requests/{membership.id}/',
            {'action': 'approve'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Step 4: Verify user is now a confirmed member
        membership.refresh_from_db()
        self.assertEqual(membership.status, 'confirmed')
        self.assertIsNotNone(membership.confirmed_at)
        self.assertIsNone(membership.rejected_at)
        self.assertTrue(membership.is_confirmed, "is_confirmed should be True after approval")
        
        # Step 5: Verify the complete flow worked
        # The user is now a confirmed member with proper status
        self.assertTrue(membership.is_confirmed)
        self.assertEqual(membership.status, 'confirmed')
        self.assertEqual(membership.role, 'member')
        
        # Verify the user can be found in the group's confirmed members
        confirmed_members = GroupMembership.objects.filter(
            group=self.group,
            status='confirmed',
            is_confirmed=True
        )
        member_usernames = [m.user.username for m in confirmed_members]
        self.assertIn('regular', member_usernames)

    def test_complete_invitation_flow(self):
        """
        Test complete invitation flow:
        1. Admin invites user
        2. User accepts invitation
        3. User becomes confirmed member
        
        Requirements: All
        """
        # Step 1: Admin invites user
        invite_data = {
            'user_id': str(self.regular_user.id),
            'role': 'member'
        }
        response = self.admin_client.post(
            f'/api/v1/groups/{self.group.id}/members/',
            invite_data,
            format='json'
        )
        # The endpoint might return 201 or 200 depending on implementation
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        
        # Verify invitation was created
        membership = GroupMembership.objects.get(
            group=self.group,
            user=self.regular_user
        )
        self.assertEqual(membership.membership_type, 'invitation')
        self.assertEqual(membership.status, 'pending')
        self.assertIsNone(membership.confirmed_at)
        
        # Step 2: User views their invitations
        response = self.user_client.get('/api/v1/groups/my-invitations/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # The response might be a list directly or in 'data'
        invitations = response.data.get('data', response.data)
        if isinstance(invitations, dict):
            invitations = invitations.get('results', [])
        self.assertEqual(len(invitations), 1)
        self.assertEqual(invitations[0]['group_name'], 'Test Group')
        self.assertEqual(invitations[0]['status'], 'pending')
        
        # Step 3: User accepts the invitation
        response = self.user_client.patch(
            f'/api/v1/groups/my-invitations/{membership.id}/',
            {'action': 'accept'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Step 4: Verify user is now a confirmed member
        membership.refresh_from_db()
        self.assertEqual(membership.status, 'confirmed')
        self.assertIsNotNone(membership.confirmed_at)
        self.assertIsNone(membership.rejected_at)
        
        # Step 5: Verify user can access group resources
        response = self.user_client.get(f'/api/v1/groups/{self.group.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_rejection_and_resend_flows(self):
        """
        Test rejection and resend flows:
        1. User requests, admin rejects, user resends
        2. Admin invites, user rejects, admin resends
        
        Requirements: 4.2, 8.3
        """
        # Flow 1: User request → Admin reject → User resend
        
        # Step 1: User requests to join
        join_request_data = {'group_name': 'Test Group'}
        response = self.user_client.post(
            '/api/v1/groups/join-request/',
            join_request_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        membership = GroupMembership.objects.get(
            group=self.group,
            user=self.regular_user
        )
        
        # Step 2: Admin rejects the request
        response = self.admin_client.patch(
            f'/api/v1/groups/{self.group.id}/join-requests/{membership.id}/',
            {'action': 'reject'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        membership.refresh_from_db()
        self.assertEqual(membership.status, 'rejected')
        self.assertIsNotNone(membership.rejected_at)
        original_rejected_at = membership.rejected_at
        
        # Step 3: User views their rejected requests
        response = self.user_client.get('/api/v1/groups/my-requests/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        requests = response.data.get('data', [])
        rejected_requests = [r for r in requests if r['status'] == 'rejected']
        self.assertEqual(len(rejected_requests), 1)
        
        # Step 4: User resends the request
        response = self.user_client.patch(
            f'/api/v1/groups/my-requests/{membership.id}/',
            {'action': 'resend'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        membership.refresh_from_db()
        self.assertEqual(membership.status, 'pending')
        self.assertIsNone(membership.rejected_at)
        self.assertIsNotNone(membership.invited_at)
        
        # Clean up for next flow
        membership.delete()
        
        # Flow 2: Admin invite → User reject → Admin resend
        
        # Step 1: Admin invites user
        invite_data = {
            'user_id': str(self.regular_user.id),
            'role': 'member'
        }
        response = self.admin_client.post(
            f'/api/v1/groups/{self.group.id}/members/',
            invite_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        membership = GroupMembership.objects.get(
            group=self.group,
            user=self.regular_user
        )
        
        # Step 2: User rejects the invitation
        response = self.user_client.patch(
            f'/api/v1/groups/my-invitations/{membership.id}/',
            {'action': 'reject'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        membership.refresh_from_db()
        self.assertEqual(membership.status, 'rejected')
        self.assertIsNotNone(membership.rejected_at)
        
        # Step 3: Admin views rejected invitations
        response = self.admin_client.get(
            f'/api/v1/groups/{self.group.id}/rejected-invitations/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        rejected_invitations = response.data['data']
        self.assertEqual(len(rejected_invitations), 1)
        
        # Step 4: Admin resends the invitation
        response = self.admin_client.patch(
            f'/api/v1/groups/{self.group.id}/rejected-invitations/{membership.id}/',
            {'action': 'resend'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        membership.refresh_from_db()
        self.assertEqual(membership.status, 'pending')
        self.assertIsNone(membership.rejected_at)

    def test_delete_operations(self):
        """
        Test delete operations:
        1. User deletes own rejected request
        2. Admin deletes rejected invitation
        3. Admin deletes rejected request
        
        Requirements: 4.3, 8.4, 9.3
        """
        # Test 1: User deletes own rejected request
        
        # Create and reject a join request
        membership1 = GroupMembership.objects.create(
            group=self.group,
            user=self.regular_user,
            membership_type='request',
            status='rejected',
            rejected_at=timezone.now()
        )
        
        # User deletes their rejected request
        response = self.user_client.patch(
            f'/api/v1/groups/my-requests/{membership1.id}/',
            {'action': 'delete'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify it's deleted
        self.assertFalse(
            GroupMembership.objects.filter(id=membership1.id).exists()
        )
        
        # Test 2: Admin deletes rejected invitation
        
        # Create another user for this test
        another_user = User.objects.create_user(
            username='another',
            email='another@test.com',
            password='Pass123!'
        )
        
        # Create and reject an invitation
        membership2 = GroupMembership.objects.create(
            group=self.group,
            user=another_user,
            membership_type='invitation',
            status='rejected',
            rejected_at=timezone.now()
        )
        
        # Admin deletes the rejected invitation
        response = self.admin_client.patch(
            f'/api/v1/groups/{self.group.id}/rejected-invitations/{membership2.id}/',
            {'action': 'delete'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify it's deleted
        self.assertFalse(
            GroupMembership.objects.filter(id=membership2.id).exists()
        )
        
        # Test 3: Admin deletes rejected request
        
        # Create yet another user
        third_user = User.objects.create_user(
            username='third',
            email='third@test.com',
            password='Pass123!'
        )
        
        # Create and reject a join request
        membership3 = GroupMembership.objects.create(
            group=self.group,
            user=third_user,
            membership_type='request',
            status='rejected',
            rejected_at=timezone.now()
        )
        
        # Admin deletes the rejected request
        response = self.admin_client.patch(
            f'/api/v1/groups/{self.group.id}/rejected-requests/{membership3.id}/',
            {'action': 'delete'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify it's deleted
        self.assertFalse(
            GroupMembership.objects.filter(id=membership3.id).exists()
        )

    def test_validation_and_error_cases(self):
        """
        Test validation and error cases:
        1. Invalid group names
        2. Duplicate requests
        3. Already member scenarios
        4. Permission errors
        
        Requirements: 2.3, 2.4, 2.5, 6.4, 6.5, 6.6
        """
        # Test 1: Invalid group name
        join_request_data = {'group_name': 'NonExistentGroup'}
        response = self.user_client.post(
            '/api/v1/groups/join-request/',
            join_request_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Check for 'errors' key in response
        self.assertTrue('errors' in response.data or 'error' in response.data)
        
        # Test 2: Duplicate request
        
        # Create initial request
        join_request_data = {'group_name': 'Test Group'}
        response = self.user_client.post(
            '/api/v1/groups/join-request/',
            join_request_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Try to create duplicate
        response = self.user_client.post(
            '/api/v1/groups/join-request/',
            join_request_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('errors' in response.data or 'error' in response.data)
        
        # Clean up
        GroupMembership.objects.filter(
            group=self.group,
            user=self.regular_user
        ).delete()
        
        # Test 3: Already member scenario
        
        # Make user a confirmed member
        GroupMembership.objects.create(
            group=self.group,
            user=self.regular_user,
            membership_type='invitation',
            status='confirmed',
            confirmed_at=timezone.now()
        )
        
        # Try to request to join
        response = self.user_client.post(
            '/api/v1/groups/join-request/',
            join_request_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('errors' in response.data or 'error' in response.data)
        
        # Clean up
        GroupMembership.objects.filter(
            group=self.group,
            user=self.regular_user
        ).delete()
        
        # Test 4: Permission errors - non-admin trying to approve requests
        
        # Create a join request
        membership = GroupMembership.objects.create(
            group=self.group,
            user=self.regular_user,
            membership_type='request',
            status='pending'
        )
        
        # Create another regular user
        another_user = User.objects.create_user(
            username='another',
            email='another@test.com',
            password='Pass123!'
        )
        another_client = APIClient()
        another_client.force_authenticate(user=another_user)
        
        # Make them a regular member
        GroupMembership.objects.create(
            group=self.group,
            user=another_user,
            membership_type='invitation',
            status='confirmed',
            confirmed_at=timezone.now()
        )
        
        # Try to approve request as non-admin
        response = another_client.patch(
            f'/api/v1/groups/{self.group.id}/join-requests/{membership.id}/',
            {'action': 'approve'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Test 5: Invalid user invitation
        
        # Try to invite non-existent user
        invite_data = {
            'user_id': '00000000-0000-0000-0000-000000000000',
            'role': 'member'
        }
        response = self.admin_client.post(
            f'/api/v1/groups/{self.group.id}/members/',
            invite_data,
            format='json'
        )
        # Either 400 or 404 is acceptable for non-existent user
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND])
        
        # Test 6: Duplicate invitation
        
        # Clean up existing memberships
        GroupMembership.objects.filter(
            group=self.group,
            user=self.regular_user
        ).delete()
        
        # Create initial invitation
        invite_data = {
            'user_id': str(self.regular_user.id),
            'role': 'member'
        }
        response = self.admin_client.post(
            f'/api/v1/groups/{self.group.id}/members/',
            invite_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Try to create duplicate invitation
        response = self.admin_client.post(
            f'/api/v1/groups/{self.group.id}/members/',
            invite_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
