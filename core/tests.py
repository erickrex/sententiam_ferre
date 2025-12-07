from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from core.models import UserAccount


class AuthenticationEndpointTests(APITestCase):
    """Test authentication endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.signup_url = reverse('auth-signup')
        self.login_url = reverse('auth-login')
        self.logout_url = reverse('auth-logout')
        self.me_url = reverse('auth-me')
        
        # Create a test user for login tests
        self.test_user = UserAccount.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
    
    def test_signup_success(self):
        """Test successful user registration"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'NewPass123!',
            'password_confirm': 'NewPass123!'
        }
        
        response = self.client.post(self.signup_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'success')
        self.assertIn('token', response.data['data'])
        self.assertIn('user', response.data['data'])
        self.assertEqual(response.data['data']['user']['username'], 'newuser')
        self.assertEqual(response.data['data']['user']['email'], 'newuser@example.com')
        
        # Verify user was created in database
        self.assertTrue(UserAccount.objects.filter(username='newuser').exists())
    
    def test_signup_password_mismatch(self):
        """Test registration fails when passwords don't match"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'NewPass123!',
            'password_confirm': 'DifferentPass123!'
        }
        
        response = self.client.post(self.signup_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], 'error')
        self.assertIn('errors', response.data)
    
    def test_signup_weak_password(self):
        """Test registration fails with password less than 4 characters"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': '123',  # Only 3 characters - should fail
            'password_confirm': '123'
        }
        
        response = self.client.post(self.signup_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], 'error')
        self.assertIn('errors', response.data)
    
    def test_signup_duplicate_username(self):
        """Test registration fails with duplicate username"""
        data = {
            'username': 'testuser',  # Already exists
            'email': 'different@example.com',
            'password': 'NewPass123!',
            'password_confirm': 'NewPass123!'
        }
        
        response = self.client.post(self.signup_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], 'error')
    
    def test_signup_duplicate_email(self):
        """Test registration fails with duplicate email"""
        data = {
            'username': 'differentuser',
            'email': 'test@example.com',  # Already exists
            'password': 'NewPass123!',
            'password_confirm': 'NewPass123!'
        }
        
        response = self.client.post(self.signup_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], 'error')
    
    def test_login_success(self):
        """Test successful login"""
        data = {
            'username': 'testuser',
            'password': 'TestPass123!'
        }
        
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertIn('token', response.data['data'])
        self.assertIn('user', response.data['data'])
        self.assertEqual(response.data['data']['user']['username'], 'testuser')
    
    def test_login_invalid_credentials(self):
        """Test login fails with invalid credentials"""
        data = {
            'username': 'testuser',
            'password': 'WrongPassword123!'
        }
        
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['status'], 'error')
        self.assertEqual(response.data['message'], 'Invalid credentials')
    
    def test_login_nonexistent_user(self):
        """Test login fails with nonexistent user"""
        data = {
            'username': 'nonexistent',
            'password': 'SomePass123!'
        }
        
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['status'], 'error')
    
    def test_logout_success(self):
        """Test successful logout"""
        # Create token for test user
        token = Token.objects.create(user=self.test_user)
        
        # Authenticate with token
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        
        response = self.client.post(self.logout_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        
        # Verify token was deleted
        self.assertFalse(Token.objects.filter(user=self.test_user).exists())
    
    def test_logout_unauthenticated(self):
        """Test logout fails without authentication"""
        response = self.client.post(self.logout_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_me_success(self):
        """Test getting current user profile"""
        # Create token for test user
        token = Token.objects.create(user=self.test_user)
        
        # Authenticate with token
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        
        response = self.client.get(self.me_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['data']['username'], 'testuser')
        self.assertEqual(response.data['data']['email'], 'test@example.com')
    
    def test_me_unauthenticated(self):
        """Test getting current user fails without authentication"""
        response = self.client.get(self.me_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PasswordHashingTests(TestCase):
    """Test password hashing functionality"""
    
    def test_password_is_hashed(self):
        """Test that passwords are hashed and not stored in plaintext"""
        password = 'TestPass123!'
        user = UserAccount.objects.create_user(
            username='testuser',
            email='test@example.com',
            password=password
        )
        
        # Password should not equal the plaintext
        self.assertNotEqual(user.password, password)
        
        # Password should be hashed (starts with algorithm identifier)
        self.assertTrue(user.password.startswith('argon2') or user.password.startswith('pbkdf2'))
    
    def test_password_verification(self):
        """Test that hashed passwords can be verified"""
        password = 'TestPass123!'
        user = UserAccount.objects.create_user(
            username='testuser',
            email='test@example.com',
            password=password
        )
        
        # Verify correct password
        self.assertTrue(user.check_password(password))
        
        # Verify incorrect password fails
        self.assertFalse(user.check_password('WrongPassword'))



class GroupManagementTests(APITestCase):
    """Test group management endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create test users
        self.user1 = UserAccount.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='TestPass123!'
        )
        self.user2 = UserAccount.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='TestPass123!'
        )
        self.user3 = UserAccount.objects.create_user(
            username='user3',
            email='user3@example.com',
            password='TestPass123!'
        )
        
        # Create tokens
        self.token1 = Token.objects.create(user=self.user1)
        self.token2 = Token.objects.create(user=self.user2)
        self.token3 = Token.objects.create(user=self.user3)
        
        self.groups_url = reverse('group-list')
    
    def test_create_group_success(self):
        """Test successful group creation"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        
        data = {
            'name': 'Test Group',
            'description': 'A test group'
        }
        
        response = self.client.post(self.groups_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['data']['name'], 'Test Group')
        self.assertEqual(response.data['data']['created_by']['username'], 'user1')
        
        # Verify creator is added as confirmed admin member
        from core.models import AppGroup, GroupMembership
        group = AppGroup.objects.get(name='Test Group')
        membership = GroupMembership.objects.get(group=group, user=self.user1)
        self.assertTrue(membership.is_confirmed)
        self.assertEqual(membership.role, 'admin')
        self.assertIsNotNone(membership.confirmed_at)
    
    def test_create_group_unauthenticated(self):
        """Test group creation fails without authentication"""
        data = {
            'name': 'Test Group',
            'description': 'A test group'
        }
        
        response = self.client.post(self.groups_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_list_user_groups(self):
        """Test listing user's groups"""
        from core.models import AppGroup, GroupMembership
        from django.utils import timezone
        
        # Create groups
        group1 = AppGroup.objects.create(
            name='Group 1',
            created_by=self.user1
        )
        group2 = AppGroup.objects.create(
            name='Group 2',
            created_by=self.user2
        )
        
        # Add user1 to both groups as confirmed member
        GroupMembership.objects.create(
            group=group1,
            user=self.user1,
            role='admin',
            is_confirmed=True,
            confirmed_at=timezone.now()
        )
        GroupMembership.objects.create(
            group=group2,
            user=self.user1,
            role='member',
            is_confirmed=True,
            confirmed_at=timezone.now()
        )
        
        # Add user2 to group2 as confirmed member
        GroupMembership.objects.create(
            group=group2,
            user=self.user2,
            role='admin',
            is_confirmed=True,
            confirmed_at=timezone.now()
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        response = self.client.get(self.groups_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(len(response.data['data']), 2)
    
    def test_get_group_details(self):
        """Test getting group details"""
        from core.models import AppGroup, GroupMembership
        from django.utils import timezone
        
        group = AppGroup.objects.create(
            name='Test Group',
            created_by=self.user1
        )
        GroupMembership.objects.create(
            group=group,
            user=self.user1,
            role='admin',
            is_confirmed=True,
            confirmed_at=timezone.now()
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        url = reverse('group-detail', kwargs={'pk': group.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['data']['name'], 'Test Group')
        self.assertIn('members', response.data['data'])
    
    def test_invite_user_to_group(self):
        """Test inviting a user to a group"""
        from core.models import AppGroup, GroupMembership
        from django.utils import timezone
        
        group = AppGroup.objects.create(
            name='Test Group',
            created_by=self.user1
        )
        GroupMembership.objects.create(
            group=group,
            user=self.user1,
            role='admin',
            is_confirmed=True,
            confirmed_at=timezone.now()
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        url = reverse('group-members', kwargs={'pk': group.id})
        
        data = {
            'user_id': str(self.user2.id),
            'role': 'member'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'success')
        
        # Verify invitation was created with new fields
        invitation = GroupMembership.objects.get(group=group, user=self.user2)
        self.assertEqual(invitation.status, 'pending')
        self.assertEqual(invitation.membership_type, 'invitation')
        self.assertEqual(invitation.role, 'member')
    
    def test_accept_invitation(self):
        """Test accepting a group invitation"""
        from core.models import AppGroup, GroupMembership
        from django.utils import timezone
        
        group = AppGroup.objects.create(
            name='Test Group',
            created_by=self.user1
        )
        GroupMembership.objects.create(
            group=group,
            user=self.user1,
            role='admin',
            is_confirmed=True,
            confirmed_at=timezone.now()
        )
        
        # Create pending invitation
        invitation = GroupMembership.objects.create(
            group=group,
            user=self.user2,
            role='member',
            is_confirmed=False
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token2.key}')
        url = reverse('group-manage-member', kwargs={'pk': group.id, 'user_id': self.user2.id})
        
        data = {'action': 'accept'}
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        
        # Verify invitation was accepted
        invitation.refresh_from_db()
        self.assertTrue(invitation.is_confirmed)
        self.assertIsNotNone(invitation.confirmed_at)
    
    def test_decline_invitation(self):
        """Test declining a group invitation"""
        from core.models import AppGroup, GroupMembership
        from django.utils import timezone
        
        group = AppGroup.objects.create(
            name='Test Group',
            created_by=self.user1
        )
        GroupMembership.objects.create(
            group=group,
            user=self.user1,
            role='admin',
            is_confirmed=True,
            confirmed_at=timezone.now()
        )
        
        # Create pending invitation
        invitation = GroupMembership.objects.create(
            group=group,
            user=self.user2,
            role='member',
            is_confirmed=False
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token2.key}')
        url = reverse('group-manage-member', kwargs={'pk': group.id, 'user_id': self.user2.id})
        
        data = {'action': 'decline'}
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        
        # Verify invitation was deleted
        self.assertFalse(GroupMembership.objects.filter(group=group, user=self.user2).exists())
    
    def test_remove_member(self):
        """Test removing a member from a group"""
        from core.models import AppGroup, GroupMembership
        from django.utils import timezone
        
        group = AppGroup.objects.create(
            name='Test Group',
            created_by=self.user1
        )
        GroupMembership.objects.create(
            group=group,
            user=self.user1,
            role='admin',
            is_confirmed=True,
            confirmed_at=timezone.now()
        )
        GroupMembership.objects.create(
            group=group,
            user=self.user2,
            role='member',
            is_confirmed=True,
            confirmed_at=timezone.now()
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        url = reverse('group-manage-member', kwargs={'pk': group.id, 'user_id': self.user2.id})
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        
        # Verify member was removed
        self.assertFalse(GroupMembership.objects.filter(group=group, user=self.user2).exists())
    
    def test_non_admin_cannot_invite(self):
        """Test that non-admin members cannot invite users"""
        from core.models import AppGroup, GroupMembership
        from django.utils import timezone
        
        group = AppGroup.objects.create(
            name='Test Group',
            created_by=self.user1
        )
        GroupMembership.objects.create(
            group=group,
            user=self.user1,
            role='admin',
            is_confirmed=True,
            confirmed_at=timezone.now()
        )
        GroupMembership.objects.create(
            group=group,
            user=self.user2,
            role='member',
            is_confirmed=True,
            confirmed_at=timezone.now()
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token2.key}')
        url = reverse('group-members', kwargs={'pk': group.id})
        
        data = {
            'user_id': str(self.user3.id),
            'role': 'member'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)



class DecisionManagementTests(APITestCase):
    """Test decision management endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create test users
        self.user1 = UserAccount.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='TestPass123!'
        )
        self.user2 = UserAccount.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='TestPass123!'
        )
        
        # Create tokens
        self.token1 = Token.objects.create(user=self.user1)
        self.token2 = Token.objects.create(user=self.user2)
        
        # Create a test group
        from core.models import AppGroup, GroupMembership
        from django.utils import timezone
        
        self.group = AppGroup.objects.create(
            name='Test Group',
            created_by=self.user1
        )
        GroupMembership.objects.create(
            group=self.group,
            user=self.user1,
            role='admin',
            is_confirmed=True,
            confirmed_at=timezone.now()
        )
        GroupMembership.objects.create(
            group=self.group,
            user=self.user2,
            role='member',
            is_confirmed=True,
            confirmed_at=timezone.now()
        )
        
        self.decisions_url = reverse('decision-list')
    
    def test_create_decision_success(self):
        """Test successful decision creation"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        
        data = {
            'group': str(self.group.id),
            'title': 'Test Decision',
            'description': 'A test decision',
            'item_type': 'restaurant',
            'rules': {'type': 'unanimous'},
            'status': 'open'
        }
        
        response = self.client.post(self.decisions_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['data']['title'], 'Test Decision')
        self.assertEqual(response.data['data']['rules'], {'type': 'unanimous'})
    
    def test_create_decision_with_threshold(self):
        """Test creating decision with threshold rules"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        
        data = {
            'group': str(self.group.id),
            'title': 'Test Decision',
            'description': 'A test decision',
            'rules': {'type': 'threshold', 'value': 0.7},
            'status': 'open'
        }
        
        response = self.client.post(self.decisions_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['data']['rules']['type'], 'threshold')
        self.assertEqual(response.data['data']['rules']['value'], 0.7)
    
    def test_create_decision_invalid_threshold(self):
        """Test creating decision with invalid threshold value"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        
        data = {
            'group': str(self.group.id),
            'title': 'Test Decision',
            'rules': {'type': 'threshold', 'value': 1.5},  # Invalid: > 1
        }
        
        response = self.client.post(self.decisions_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], 'error')
    
    def test_create_decision_non_member(self):
        """Test that non-members cannot create decisions"""
        user3 = UserAccount.objects.create_user(
            username='user3',
            email='user3@example.com',
            password='TestPass123!'
        )
        token3 = Token.objects.create(user=user3)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token3.key}')
        
        data = {
            'group': str(self.group.id),
            'title': 'Test Decision',
            'rules': {'type': 'unanimous'},
        }
        
        response = self.client.post(self.decisions_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_get_decision_details(self):
        """Test getting decision details"""
        from core.models import Decision
        
        decision = Decision.objects.create(
            group=self.group,
            title='Test Decision',
            description='Test',
            rules={'type': 'unanimous'},
            status='open'
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        url = reverse('decision-detail', kwargs={'pk': decision.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['data']['title'], 'Test Decision')
    
    def test_update_decision_status(self):
        """Test updating decision status"""
        from core.models import Decision
        
        decision = Decision.objects.create(
            group=self.group,
            title='Test Decision',
            rules={'type': 'unanimous'},
            status='open'
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        url = reverse('decision-detail', kwargs={'pk': decision.id})
        
        data = {'status': 'closed'}
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['data']['status'], 'closed')
    
    def test_update_decision_invalid_transition(self):
        """Test that invalid status transitions are rejected"""
        from core.models import Decision
        
        decision = Decision.objects.create(
            group=self.group,
            title='Test Decision',
            rules={'type': 'unanimous'},
            status='closed'
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        url = reverse('decision-detail', kwargs={'pk': decision.id})
        
        data = {'status': 'open'}  # Invalid: closed -> open
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], 'error')
    
    def test_non_admin_cannot_update_decision(self):
        """Test that non-admin members cannot update decisions"""
        from core.models import Decision
        
        decision = Decision.objects.create(
            group=self.group,
            title='Test Decision',
            rules={'type': 'unanimous'},
            status='open'
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token2.key}')
        url = reverse('decision-detail', kwargs={'pk': decision.id})
        
        data = {'status': 'closed'}
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_list_group_decisions(self):
        """Test listing decisions for a group"""
        from core.models import Decision
        
        Decision.objects.create(
            group=self.group,
            title='Decision 1',
            rules={'type': 'unanimous'},
            status='open'
        )
        Decision.objects.create(
            group=self.group,
            title='Decision 2',
            rules={'type': 'threshold', 'value': 0.5},
            status='draft'
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        url = reverse('group-list-decisions', kwargs={'pk': self.group.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(len(response.data['data']), 2)



class DecisionSharingTests(APITestCase):
    """Test decision sharing functionality"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create test users
        self.user1 = UserAccount.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='TestPass123!'
        )
        self.user2 = UserAccount.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='TestPass123!'
        )
        
        # Create tokens
        self.token1 = Token.objects.create(user=self.user1)
        self.token2 = Token.objects.create(user=self.user2)
        
        # Create test groups
        from core.models import AppGroup, GroupMembership
        from django.utils import timezone
        
        self.group1 = AppGroup.objects.create(
            name='Group 1',
            created_by=self.user1
        )
        GroupMembership.objects.create(
            group=self.group1,
            user=self.user1,
            role='admin',
            is_confirmed=True,
            confirmed_at=timezone.now()
        )
        
        self.group2 = AppGroup.objects.create(
            name='Group 2',
            created_by=self.user2
        )
        GroupMembership.objects.create(
            group=self.group2,
            user=self.user2,
            role='admin',
            is_confirmed=True,
            confirmed_at=timezone.now()
        )
    
    def test_share_decision_success(self):
        """Test successfully sharing a decision with another group"""
        from core.models import Decision
        
        decision = Decision.objects.create(
            group=self.group1,
            title='Test Decision',
            rules={'type': 'unanimous'},
            status='open'
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        url = reverse('decision-share-group', kwargs={'pk': decision.id})
        
        data = {'group_id': str(self.group2.id)}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'success')
        
        # Verify share was created
        from core.models import DecisionSharedGroup
        self.assertTrue(
            DecisionSharedGroup.objects.filter(
                decision=decision,
                group=self.group2
            ).exists()
        )
    
    def test_shared_decision_access(self):
        """Test that users in shared groups can access the decision"""
        from core.models import Decision, DecisionSharedGroup
        
        decision = Decision.objects.create(
            group=self.group1,
            title='Test Decision',
            rules={'type': 'unanimous'},
            status='open'
        )
        
        # Share with group2
        DecisionSharedGroup.objects.create(
            decision=decision,
            group=self.group2
        )
        
        # User2 should be able to access the decision
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token2.key}')
        url = reverse('decision-detail', kwargs={'pk': decision.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['data']['title'], 'Test Decision')
    
    def test_non_admin_cannot_share(self):
        """Test that non-admin members cannot share decisions"""
        from core.models import Decision, GroupMembership
        from django.utils import timezone
        
        # Add user2 as regular member to group1
        GroupMembership.objects.create(
            group=self.group1,
            user=self.user2,
            role='member',
            is_confirmed=True,
            confirmed_at=timezone.now()
        )
        
        decision = Decision.objects.create(
            group=self.group1,
            title='Test Decision',
            rules={'type': 'unanimous'},
            status='open'
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token2.key}')
        url = reverse('decision-share-group', kwargs={'pk': decision.id})
        
        data = {'group_id': str(self.group2.id)}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_cannot_share_twice(self):
        """Test that a decision cannot be shared with the same group twice"""
        from core.models import Decision, DecisionSharedGroup
        
        decision = Decision.objects.create(
            group=self.group1,
            title='Test Decision',
            rules={'type': 'unanimous'},
            status='open'
        )
        
        # Share once
        DecisionSharedGroup.objects.create(
            decision=decision,
            group=self.group2
        )
        
        # Try to share again
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token1.key}')
        url = reverse('decision-share-group', kwargs={'pk': decision.id})
        
        data = {'group_id': str(self.group2.id)}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
