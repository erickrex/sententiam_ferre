"""
Comprehensive End-to-End Testing for Group Invitation-Requests Feature

This test suite performs ULTRA-CRITICAL validation of the entire system:
- Database integrity across all operations
- API endpoint chains and state transitions
- Authorization and permission boundaries
- Data consistency and constraint enforcement
- Edge cases and error handling
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from core.models import AppGroup, GroupMembership
from django.utils import timezone
from django.db import connection
from django.db.models import Q, Count

User = get_user_model()


class ComprehensiveE2ETests(TestCase):
    """Ultra-critical end-to-end validation tests"""

    def setUp(self):
        """Set up comprehensive test environment"""
        from rest_framework.authtoken.models import Token
        
        # Create multiple users for complex scenarios
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='AdminPass123!'
        )
        
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@test.com',
            password='UserPass123!'
        )
        
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@test.com',
            password='UserPass123!'
        )
        
        self.user3 = User.objects.create_user(
            username='user3',
            email='user3@test.com',
            password='UserPass123!'
        )
        
        # Create API clients
        self.admin_client = APIClient()
        self.user1_client = APIClient()
        self.user2_client = APIClient()
        self.user3_client = APIClient()
        
        # Authenticate all clients
        admin_token, _ = Token.objects.get_or_create(user=self.admin_user)
        user1_token, _ = Token.objects.get_or_create(user=self.user1)
        user2_token, _ = Token.objects.get_or_create(user=self.user2)
        user3_token, _ = Token.objects.get_or_create(user=self.user3)
        
        self.admin_client.credentials(HTTP_AUTHORIZATION=f'Token {admin_token.key}')
        self.user1_client.credentials(HTTP_AUTHORIZATION=f'Token {user1_token.key}')
        self.user2_client.credentials(HTTP_AUTHORIZATION=f'Token {user2_token.key}')
        self.user3_client.credentials(HTTP_AUTHORIZATION=f'Token {user3_token.key}')
        
        # Create test groups
        self.group1 = AppGroup.objects.create(
            name='Group Alpha',
            description='First test group',
            created_by=self.admin_user
        )
        
        self.group2 = AppGroup.objects.create(
            name='Group Beta',
            description='Second test group',
            created_by=self.admin_user
        )
        
        # Make admin user an admin member of both groups
        for group in [self.group1, self.group2]:
            GroupMembership.objects.create(
                group=group,
                user=self.admin_user,
                role='admin',
                membership_type='invitation',
                status='confirmed',
                is_confirmed=True,
                confirmed_at=timezone.now()
            )

    
    def verify_database_integrity(self):
        """Verify database constraints and indexes are working"""
        # Check unique constraint on (group, user)
        memberships = GroupMembership.objects.values('group', 'user').annotate(
            count=Count('id')
        )
        for m in memberships:
            self.assertEqual(m['count'], 1, 
                f"Duplicate membership found for group {m['group']}, user {m['user']}")
        
        # Verify all memberships have required fields
        invalid_memberships = GroupMembership.objects.filter(
            Q(membership_type__isnull=True) | 
            Q(status__isnull=True)
        )
        self.assertEqual(invalid_memberships.count(), 0, 
            "Found memberships with null required fields")
        
        # Verify status transitions are valid
        for membership in GroupMembership.objects.all():
            self.assertIn(membership.status, ['pending', 'confirmed', 'rejected'])
            self.assertIn(membership.membership_type, ['invitation', 'request'])
            
            if membership.status == 'confirmed':
                self.assertIsNotNone(membership.confirmed_at, 
                    f"Confirmed membership {membership.id} missing confirmed_at")
            
            if membership.status == 'rejected':
                self.assertIsNotNone(membership.rejected_at,
                    f"Rejected membership {membership.id} missing rejected_at")

    def test_ultra_critical_complete_workflow(self):
        """
        ULTRA-CRITICAL: Test complete workflow with all state transitions
        
        This test validates:
        1. User join request creation and validation
        2. Admin approval workflow
        3. Invitation creation and acceptance
        4. Rejection and resend flows
        5. Delete operations
        6. Database integrity throughout
        """
        from django.db.models import Count
        
        print("\n=== STARTING ULTRA-CRITICAL E2E TEST ===\n")
        
        # ===== PHASE 1: JOIN REQUEST FLOW =====
        print("PHASE 1: Testing join request flow...")
        
        # User1 requests to join Group Alpha
        response = self.user1_client.post(
            '/api/v1/groups/join-request/',
            {'group_name': 'Group Alpha'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED,
            f"Join request creation failed: {response.data}")
        
        # Verify database state
        membership1 = GroupMembership.objects.get(
            group=self.group1,
            user=self.user1
        )
        self.assertEqual(membership1.membership_type, 'request')
        self.assertEqual(membership1.status, 'pending')
        self.assertFalse(membership1.is_confirmed)
        self.assertIsNone(membership1.confirmed_at)
        self.assertIsNone(membership1.rejected_at)
        print("✓ Join request created correctly")
        
        # Verify user can see their request
        response = self.user1_client.get('/api/v1/groups/my-requests/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        requests = response.data.get('data', [])
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0]['group_name'], 'Group Alpha')
        print("✓ User can view their join request")
        
        # Verify admin can see the request
        response = self.admin_client.get(
            f'/api/v1/groups/{self.group1.id}/join-requests/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        admin_requests = response.data['data']['results']
        self.assertEqual(len(admin_requests), 1)
        self.assertEqual(admin_requests[0]['user']['username'], 'user1')
        print("✓ Admin can view pending join requests")

        
        # Admin approves the request
        response = self.admin_client.patch(
            f'/api/v1/groups/{self.group1.id}/join-requests/{membership1.id}/',
            {'action': 'approve'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK,
            f"Join request approval failed: {response.data}")
        
        # Verify database state after approval
        membership1.refresh_from_db()
        self.assertEqual(membership1.status, 'confirmed')
        self.assertTrue(membership1.is_confirmed)
        self.assertIsNotNone(membership1.confirmed_at)
        self.assertIsNone(membership1.rejected_at)
        print("✓ Join request approved successfully")
        
        # Verify database integrity
        self.verify_database_integrity()
        print("✓ Database integrity verified after approval")
        
        # ===== PHASE 2: INVITATION FLOW =====
        print("\nPHASE 2: Testing invitation flow...")
        
        # Admin invites user2 to Group Alpha
        response = self.admin_client.post(
            f'/api/v1/groups/{self.group1.id}/members/',
            {'user_id': str(self.user2.id), 'role': 'member'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED,
            f"Invitation creation failed: {response.data}")
        
        # Verify database state
        membership2 = GroupMembership.objects.get(
            group=self.group1,
            user=self.user2
        )
        self.assertEqual(membership2.membership_type, 'invitation')
        self.assertEqual(membership2.status, 'pending')
        self.assertFalse(membership2.is_confirmed)
        print("✓ Invitation created correctly")
        
        # Verify user2 can see their invitation
        response = self.user2_client.get('/api/v1/groups/my-invitations/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        invitations = response.data.get('data', response.data)
        if isinstance(invitations, dict):
            invitations = invitations.get('results', [])
        self.assertEqual(len(invitations), 1)
        self.assertEqual(invitations[0]['group_name'], 'Group Alpha')
        print("✓ User can view their invitation")
        
        # User2 accepts the invitation
        response = self.user2_client.patch(
            f'/api/v1/groups/my-invitations/{membership2.id}/',
            {'action': 'accept'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK,
            f"Invitation acceptance failed: {response.data}")
        
        # Verify database state after acceptance
        membership2.refresh_from_db()
        self.assertEqual(membership2.status, 'confirmed')
        self.assertTrue(membership2.is_confirmed)
        self.assertIsNotNone(membership2.confirmed_at)
        print("✓ Invitation accepted successfully")
        
        # Verify database integrity
        self.verify_database_integrity()
        print("✓ Database integrity verified after acceptance")

        
        # ===== PHASE 3: REJECTION AND RESEND FLOW =====
        print("\nPHASE 3: Testing rejection and resend flow...")
        
        # User3 requests to join Group Alpha
        response = self.user3_client.post(
            '/api/v1/groups/join-request/',
            {'group_name': 'Group Alpha'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        membership3 = GroupMembership.objects.get(
            group=self.group1,
            user=self.user3
        )
        
        # Admin rejects the request
        response = self.admin_client.patch(
            f'/api/v1/groups/{self.group1.id}/join-requests/{membership3.id}/',
            {'action': 'reject'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify rejection state
        membership3.refresh_from_db()
        self.assertEqual(membership3.status, 'rejected')
        self.assertFalse(membership3.is_confirmed)
        self.assertIsNotNone(membership3.rejected_at)
        original_rejected_at = membership3.rejected_at
        print("✓ Join request rejected successfully")
        
        # Verify user3 can see their rejected request
        response = self.user3_client.get('/api/v1/groups/my-requests/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        requests = response.data.get('data', [])
        rejected = [r for r in requests if r['status'] == 'rejected']
        self.assertEqual(len(rejected), 1)
        print("✓ User can view rejected request")
        
        # User3 resends the request
        response = self.user3_client.patch(
            f'/api/v1/groups/my-requests/{membership3.id}/',
            {'action': 'resend'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK,
            f"Resend failed: {response.data}")
        
        # Verify resend state
        membership3.refresh_from_db()
        self.assertEqual(membership3.status, 'pending')
        self.assertIsNone(membership3.rejected_at)
        self.assertIsNotNone(membership3.invited_at)
        print("✓ Request resent successfully")
        
        # Admin approves the resent request
        response = self.admin_client.patch(
            f'/api/v1/groups/{self.group1.id}/join-requests/{membership3.id}/',
            {'action': 'approve'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        membership3.refresh_from_db()
        self.assertEqual(membership3.status, 'confirmed')
        self.assertTrue(membership3.is_confirmed)
        print("✓ Resent request approved successfully")
        
        # Verify database integrity
        self.verify_database_integrity()
        print("✓ Database integrity verified after resend flow")

        
        # ===== PHASE 4: DELETE OPERATIONS =====
        print("\nPHASE 4: Testing delete operations...")
        
        # Create a new user for delete testing
        user4 = User.objects.create_user(
            username='user4',
            email='user4@test.com',
            password='UserPass123!'
        )
        user4_client = APIClient()
        from rest_framework.authtoken.models import Token
        user4_token, _ = Token.objects.get_or_create(user=user4)
        user4_client.credentials(HTTP_AUTHORIZATION=f'Token {user4_token.key}')
        
        # User4 requests to join, gets rejected
        response = user4_client.post(
            '/api/v1/groups/join-request/',
            {'group_name': 'Group Alpha'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        membership4 = GroupMembership.objects.get(
            group=self.group1,
            user=user4
        )
        
        # Admin rejects
        response = self.admin_client.patch(
            f'/api/v1/groups/{self.group1.id}/join-requests/{membership4.id}/',
            {'action': 'reject'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # User4 deletes their rejected request
        response = user4_client.patch(
            f'/api/v1/groups/my-requests/{membership4.id}/',
            {'action': 'delete'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK,
            f"Delete failed: {response.data}")
        
        # Verify it's deleted from database
        self.assertFalse(
            GroupMembership.objects.filter(id=membership4.id).exists(),
            "Membership should be deleted from database"
        )
        print("✓ User successfully deleted rejected request")
        
        # Test admin deleting rejected invitation
        user5 = User.objects.create_user(
            username='user5',
            email='user5@test.com',
            password='UserPass123!'
        )
        user5_client = APIClient()
        user5_token, _ = Token.objects.get_or_create(user=user5)
        user5_client.credentials(HTTP_AUTHORIZATION=f'Token {user5_token.key}')
        
        # Admin invites user5
        response = self.admin_client.post(
            f'/api/v1/groups/{self.group1.id}/members/',
            {'user_id': str(user5.id), 'role': 'member'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        membership5 = GroupMembership.objects.get(
            group=self.group1,
            user=user5
        )
        
        # User5 rejects
        response = user5_client.patch(
            f'/api/v1/groups/my-invitations/{membership5.id}/',
            {'action': 'reject'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Admin deletes rejected invitation
        response = self.admin_client.patch(
            f'/api/v1/groups/{self.group1.id}/rejected-invitations/{membership5.id}/',
            {'action': 'delete'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK,
            f"Admin delete failed: {response.data}")
        
        # Verify it's deleted
        self.assertFalse(
            GroupMembership.objects.filter(id=membership5.id).exists(),
            "Invitation should be deleted from database"
        )
        print("✓ Admin successfully deleted rejected invitation")
        
        # Verify database integrity
        self.verify_database_integrity()
        print("✓ Database integrity verified after delete operations")

        
        # ===== PHASE 5: VALIDATION AND ERROR CASES =====
        print("\nPHASE 5: Testing validation and error cases...")
        
        # Test duplicate request prevention
        user6 = User.objects.create_user(
            username='user6',
            email='user6@test.com',
            password='UserPass123!'
        )
        user6_client = APIClient()
        user6_token, _ = Token.objects.get_or_create(user=user6)
        user6_client.credentials(HTTP_AUTHORIZATION=f'Token {user6_token.key}')
        
        # First request succeeds
        response = user6_client.post(
            '/api/v1/groups/join-request/',
            {'group_name': 'Group Alpha'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Duplicate request fails
        response = user6_client.post(
            '/api/v1/groups/join-request/',
            {'group_name': 'Group Alpha'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST,
            "Duplicate request should be rejected")
        print("✓ Duplicate request prevention working")
        
        # Test invalid group name
        response = user6_client.post(
            '/api/v1/groups/join-request/',
            {'group_name': 'NonExistentGroup'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST,
            "Invalid group name should be rejected")
        print("✓ Invalid group name validation working")
        
        # Test already member scenario
        membership6 = GroupMembership.objects.get(
            group=self.group1,
            user=user6
        )
        # Approve the request
        response = self.admin_client.patch(
            f'/api/v1/groups/{self.group1.id}/join-requests/{membership6.id}/',
            {'action': 'approve'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Try to request again as confirmed member
        response = user6_client.post(
            '/api/v1/groups/join-request/',
            {'group_name': 'Group Alpha'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST,
            "Already member should be rejected")
        print("✓ Already member validation working")
        
        # Test non-admin cannot approve requests
        user7 = User.objects.create_user(
            username='user7',
            email='user7@test.com',
            password='UserPass123!'
        )
        user7_client = APIClient()
        user7_token, _ = Token.objects.get_or_create(user=user7)
        user7_client.credentials(HTTP_AUTHORIZATION=f'Token {user7_token.key}')
        
        # Make user7 a regular member
        GroupMembership.objects.create(
            group=self.group1,
            user=user7,
            membership_type='invitation',
            status='confirmed',
            is_confirmed=True,
            confirmed_at=timezone.now()
        )
        
        # Create a pending request from another user
        user8 = User.objects.create_user(
            username='user8',
            email='user8@test.com',
            password='UserPass123!'
        )
        membership8 = GroupMembership.objects.create(
            group=self.group1,
            user=user8,
            membership_type='request',
            status='pending'
        )
        
        # User7 (non-admin) tries to approve
        response = user7_client.patch(
            f'/api/v1/groups/{self.group1.id}/join-requests/{membership8.id}/',
            {'action': 'approve'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN,
            "Non-admin should not be able to approve requests")
        print("✓ Non-admin authorization check working")
        
        # Verify database integrity after all operations
        self.verify_database_integrity()
        print("✓ Database integrity verified after validation tests")

        
        # ===== PHASE 6: CROSS-GROUP OPERATIONS =====
        print("\nPHASE 6: Testing cross-group operations...")
        
        # Verify user can be member of multiple groups
        user9 = User.objects.create_user(
            username='user9',
            email='user9@test.com',
            password='UserPass123!'
        )
        user9_client = APIClient()
        user9_token, _ = Token.objects.get_or_create(user=user9)
        user9_client.credentials(HTTP_AUTHORIZATION=f'Token {user9_token.key}')
        
        # Request to join both groups
        response = user9_client.post(
            '/api/v1/groups/join-request/',
            {'group_name': 'Group Alpha'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        response = user9_client.post(
            '/api/v1/groups/join-request/',
            {'group_name': 'Group Beta'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify both requests exist
        memberships = GroupMembership.objects.filter(user=user9)
        self.assertEqual(memberships.count(), 2)
        print("✓ User can request to join multiple groups")
        
        # Approve both
        for membership in memberships:
            response = self.admin_client.patch(
                f'/api/v1/groups/{membership.group.id}/join-requests/{membership.id}/',
                {'action': 'approve'},
                format='json'
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify user is confirmed member of both groups
        confirmed_memberships = GroupMembership.objects.filter(
            user=user9,
            status='confirmed',
            is_confirmed=True
        )
        self.assertEqual(confirmed_memberships.count(), 2)
        print("✓ User successfully joined multiple groups")
        
        # Verify database integrity
        self.verify_database_integrity()
        print("✓ Database integrity verified for cross-group operations")
        
        # ===== PHASE 7: FINAL VERIFICATION =====
        print("\nPHASE 7: Final system verification...")
        
        # Count all memberships
        total_memberships = GroupMembership.objects.count()
        confirmed_memberships = GroupMembership.objects.filter(
            status='confirmed',
            is_confirmed=True
        ).count()
        pending_memberships = GroupMembership.objects.filter(
            status='pending'
        ).count()
        rejected_memberships = GroupMembership.objects.filter(
            status='rejected'
        ).count()
        
        print(f"  Total memberships: {total_memberships}")
        print(f"  Confirmed: {confirmed_memberships}")
        print(f"  Pending: {pending_memberships}")
        print(f"  Rejected: {rejected_memberships}")
        
        # Verify no orphaned data
        self.assertEqual(
            total_memberships,
            confirmed_memberships + pending_memberships + rejected_memberships,
            "Membership counts don't add up"
        )
        
        # Verify all confirmed members have proper timestamps
        for membership in GroupMembership.objects.filter(status='confirmed'):
            self.assertIsNotNone(membership.confirmed_at,
                f"Confirmed membership {membership.id} missing confirmed_at")
            self.assertTrue(membership.is_confirmed,
                f"Confirmed membership {membership.id} has is_confirmed=False")
        
        # Verify all rejected members have proper timestamps
        for membership in GroupMembership.objects.filter(status='rejected'):
            self.assertIsNotNone(membership.rejected_at,
                f"Rejected membership {membership.id} missing rejected_at")
        
        # Final database integrity check
        self.verify_database_integrity()
        
        print("\n=== ALL ULTRA-CRITICAL E2E TESTS PASSED ===\n")
