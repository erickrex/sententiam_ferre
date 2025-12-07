"""
Integration tests for admin request management endpoints.
"""

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from core.models import UserAccount, AppGroup, GroupMembership


class AdminRequestManagementEndpointsTest(TestCase):
    """Test admin request management endpoints"""
    
    def setUp(self):
        """Set up test data"""
        # Create users
        self.admin_user = UserAccount.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123'
        )
        
        self.regular_user = UserAccount.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='testpass123'
        )
        
        self.requester1 = UserAccount.objects.create_user(
            username='requester1',
            email='requester1@example.com',
            password='testpass123'
        )
        
        self.requester2 = UserAccount.objects.create_user(
            username='requester2',
            email='requester2@example.com',
            password='testpass123'
        )
        
        self.invited_user = UserAccount.objects.create_user(
            username='invited',
            email='invited@example.com',
            password='testpass123'
        )
        
        # Create group
        self.group = AppGroup.objects.create(
            name='Test Group',
            description='Test group for admin endpoints',
            created_by=self.admin_user
        )
        
        # Create admin membership
        GroupMembership.objects.create(
            group=self.group,
            user=self.admin_user,
            role='admin',
            membership_type='invitation',
            status='confirmed',
            is_confirmed=True,
            confirmed_at=timezone.now()
        )
        
        # Create regular member
        GroupMembership.objects.create(
            group=self.group,
            user=self.regular_user,
            role='member',
            membership_type='invitation',
            status='confirmed',
            is_confirmed=True,
            confirmed_at=timezone.now()
        )
        
        # Create pending join requests
        self.pending_request1 = GroupMembership.objects.create(
            group=self.group,
            user=self.requester1,
            role='member',
            membership_type='request',
            status='pending',
            is_confirmed=False
        )
        
        self.pending_request2 = GroupMembership.objects.create(
            group=self.group,
            user=self.requester2,
            role='member',
            membership_type='request',
            status='pending',
            is_confirmed=False
        )
        
        # Create rejected invitation
        self.rejected_invitation = GroupMembership.objects.create(
            group=self.group,
            user=self.invited_user,
            role='member',
            membership_type='invitation',
            status='rejected',
            is_confirmed=False,
            rejected_at=timezone.now()
        )
        
        # Set up API client
        self.client = APIClient()
    
    def test_list_join_requests_as_admin(self):
        """Test that admin can list pending join requests"""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get(f'/api/v1/groups/{self.group.id}/join-requests/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['data']['count'], 2)
        self.assertEqual(len(response.data['data']['results']), 2)
    
    def test_list_join_requests_as_non_admin(self):
        """Test that non-admin cannot list join requests"""
        self.client.force_authenticate(user=self.regular_user)
        
        response = self.client.get(f'/api/v1/groups/{self.group.id}/join-requests/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_approve_join_request(self):
        """Test that admin can approve a join request"""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.patch(
            f'/api/v1/groups/{self.group.id}/join-requests/{self.pending_request1.id}/',
            {'action': 'approve'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['message'], 'Request approved')
        
        # Verify the request was approved
        self.pending_request1.refresh_from_db()
        self.assertEqual(self.pending_request1.status, 'confirmed')
        self.assertTrue(self.pending_request1.is_confirmed)
        self.assertIsNotNone(self.pending_request1.confirmed_at)
    
    def test_reject_join_request(self):
        """Test that admin can reject a join request"""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.patch(
            f'/api/v1/groups/{self.group.id}/join-requests/{self.pending_request2.id}/',
            {'action': 'reject'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['message'], 'Request rejected')
        
        # Verify the request was rejected
        self.pending_request2.refresh_from_db()
        self.assertEqual(self.pending_request2.status, 'rejected')
        self.assertFalse(self.pending_request2.is_confirmed)
        self.assertIsNotNone(self.pending_request2.rejected_at)
    
    def test_list_rejected_invitations(self):
        """Test that admin can list rejected invitations"""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get(f'/api/v1/groups/{self.group.id}/rejected-invitations/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['id'], str(self.rejected_invitation.id))
    
    def test_resend_rejected_invitation(self):
        """Test that admin can resend a rejected invitation"""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.patch(
            f'/api/v1/groups/{self.group.id}/rejected-invitations/{self.rejected_invitation.id}/',
            {'action': 'resend'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['message'], 'Invitation resent')
        
        # Verify the invitation was resent
        self.rejected_invitation.refresh_from_db()
        self.assertEqual(self.rejected_invitation.status, 'pending')
        self.assertIsNone(self.rejected_invitation.rejected_at)
    
    def test_delete_rejected_invitation(self):
        """Test that admin can delete a rejected invitation"""
        self.client.force_authenticate(user=self.admin_user)
        
        invitation_id = self.rejected_invitation.id
        
        response = self.client.patch(
            f'/api/v1/groups/{self.group.id}/rejected-invitations/{invitation_id}/',
            {'action': 'delete'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['message'], 'Record deleted successfully')
        
        # Verify the invitation was deleted
        self.assertFalse(GroupMembership.objects.filter(id=invitation_id).exists())
    
    def test_list_rejected_requests(self):
        """Test that admin can list rejected requests"""
        # First reject a request
        self.pending_request1.status = 'rejected'
        self.pending_request1.rejected_at = timezone.now()
        self.pending_request1.save()
        
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get(f'/api/v1/groups/{self.group.id}/rejected-requests/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['id'], str(self.pending_request1.id))
    
    def test_delete_rejected_request(self):
        """Test that admin can delete a rejected request"""
        # First reject a request
        self.pending_request1.status = 'rejected'
        self.pending_request1.rejected_at = timezone.now()
        self.pending_request1.save()
        
        self.client.force_authenticate(user=self.admin_user)
        
        request_id = self.pending_request1.id
        
        response = self.client.patch(
            f'/api/v1/groups/{self.group.id}/rejected-requests/{request_id}/',
            {'action': 'delete'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['message'], 'Record deleted successfully')
        
        # Verify the request was deleted
        self.assertFalse(GroupMembership.objects.filter(id=request_id).exists())
    
    def test_cannot_resend_rejected_request(self):
        """Test that admin cannot resend a rejected request (only users can)"""
        # First reject a request
        self.pending_request1.status = 'rejected'
        self.pending_request1.rejected_at = timezone.now()
        self.pending_request1.save()
        
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.patch(
            f'/api/v1/groups/{self.group.id}/rejected-requests/{self.pending_request1.id}/',
            {'action': 'resend'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Only "delete" is allowed', response.data['message'])
