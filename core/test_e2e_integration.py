"""
End-to-end integration tests for complete user workflows.

Tests the complete user journey from signup through voting and favourites.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from core.models import (
    AppGroup, GroupMembership, Decision, DecisionItem, 
    DecisionVote, DecisionSelection, Conversation, Message,
    Taxonomy, Term, DecisionItemTerm
)
import json

User = get_user_model()


class EndToEndIntegrationTests(TestCase):
    """
    End-to-end integration tests covering complete user workflows.
    Tests: signup → create group → invite → create decision → add items → vote → see favourites
    """

    def setUp(self):
        """Set up test clients for multiple users"""
        self.client1 = APIClient()
        self.client2 = APIClient()
        self.client3 = APIClient()
        self.client_non_member = APIClient()

    def test_complete_user_flow(self):
        """
        Test complete user flow: signup → create group → invite → create decision → 
        add items → vote → see favourites
        """
        # Step 1: User signup
        signup_data_1 = {
            'username': 'organizer',
            'email': 'organizer@test.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!'
        }
        response = self.client1.post('/api/v1/auth/signup/', signup_data_1, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        token1 = response.data['data']['token']
        self.client1.credentials(HTTP_AUTHORIZATION=f'Token {token1}')

        # Step 2: Second user signup
        signup_data_2 = {
            'username': 'participant1',
            'email': 'participant1@test.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!'
        }
        response = self.client2.post('/api/v1/auth/signup/', signup_data_2, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        token2 = response.data['data']['token']
        self.client2.credentials(HTTP_AUTHORIZATION=f'Token {token2}')

        # Step 3: Third user signup
        signup_data_3 = {
            'username': 'participant2',
            'email': 'participant2@test.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!'
        }
        response = self.client3.post('/api/v1/auth/signup/', signup_data_3, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        token3 = response.data['data']['token']
        self.client3.credentials(HTTP_AUTHORIZATION=f'Token {token3}')

        # Step 4: Create group
        group_data = {
            'name': 'Test Group',
            'description': 'A test group for decision making'
        }
        response = self.client1.post('/api/v1/groups/', group_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        group_id = response.data.get('id') or response.data.get('data', {}).get('id')

        # Verify organizer is auto-member
        memberships = GroupMembership.objects.filter(
            group_id=group_id,
            user__username='organizer'
        )
        self.assertEqual(memberships.count(), 1)
        self.assertTrue(memberships.first().is_confirmed)

        # Step 5: Invite users to group
        user2 = User.objects.get(username='participant1')
        user3 = User.objects.get(username='participant2')

        invite_data_2 = {'user_id': str(user2.id), 'role': 'member'}
        response = self.client1.post(f'/api/v1/groups/{group_id}/members/', invite_data_2, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        invite_data_3 = {'user_id': str(user3.id), 'role': 'member'}
        response = self.client1.post(f'/api/v1/groups/{group_id}/members/', invite_data_3, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Step 6: Accept invitations
        response = self.client2.patch(
            f'/api/v1/groups/{group_id}/members/{user2.id}/',
            {'action': 'accept'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client3.patch(
            f'/api/v1/groups/{group_id}/members/{user3.id}/',
            {'action': 'accept'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Step 7: Create decision with threshold rule
        decision_data = {
            'group': str(group_id),
            'title': 'Choose Restaurant',
            'description': 'Where should we eat?',
            'item_type': 'restaurant',
            'rules': {'type': 'threshold', 'value': 0.67},  # 2 out of 3 votes
            'status': 'open'
        }
        response = self.client1.post('/api/v1/decisions/', decision_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        decision_id = response.data.get('id') or response.data.get('data', {}).get('id')

        # Step 8: Add items to decision
        items_data = [
            {'decision': str(decision_id), 'label': 'Italian Restaurant', 'attributes': {'cuisine': 'italian', 'price': 30}},
            {'decision': str(decision_id), 'label': 'Japanese Restaurant', 'attributes': {'cuisine': 'japanese', 'price': 40}},
            {'decision': str(decision_id), 'label': 'Mexican Restaurant', 'attributes': {'cuisine': 'mexican', 'price': 25}}
        ]

        item_ids = []
        for item_data in items_data:
            response = self.client1.post('/api/v1/items/', item_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            item_id = response.data.get('id') or response.data.get('data', {}).get('id')
            item_ids.append(item_id)

        # Step 9: Vote on items
        # User 1 likes Italian and Japanese
        response = self.client1.post(f'/api/v1/votes/items/{item_ids[0]}/votes/', {'is_like': True}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client1.post(f'/api/v1/votes/items/{item_ids[1]}/votes/', {'is_like': True}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client1.post(f'/api/v1/votes/items/{item_ids[2]}/votes/', {'is_like': False}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # User 2 likes Italian and Mexican
        response = self.client2.post(f'/api/v1/votes/items/{item_ids[0]}/votes/', {'is_like': True}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client2.post(f'/api/v1/votes/items/{item_ids[1]}/votes/', {'is_like': False}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client2.post(f'/api/v1/votes/items/{item_ids[2]}/votes/', {'is_like': True}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # User 3 likes Italian (this should trigger favourite for Italian: 3/3 = 100% > 67%)
        response = self.client3.post(f'/api/v1/votes/items/{item_ids[0]}/votes/', {'is_like': True}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Step 10: Check favourites
        response = self.client1.get(f'/api/v1/decisions/{decision_id}/favourites/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Italian should be in favourites (3/3 votes)
        favourites = response.data if isinstance(response.data, list) else response.data.get('data', [])
        self.assertGreater(len(favourites), 0)
        favourite_labels = [f.get('item', {}).get('label') or f.get('label') for f in favourites]
        self.assertIn('Italian Restaurant', favourite_labels)

        # Step 11: Verify favourites in database
        selections = DecisionSelection.objects.filter(decision_id=decision_id)
        self.assertGreater(selections.count(), 0)
        
        italian_item = DecisionItem.objects.get(id=item_ids[0])
        italian_selection = selections.filter(item=italian_item).first()
        self.assertIsNotNone(italian_selection)
        self.assertIsNotNone(italian_selection.snapshot)

    def test_chat_functionality_across_users(self):
        """Test chat functionality with multiple users sending and receiving messages"""
        # Setup: Create users, group, and decision
        user1 = User.objects.create_user(username='user1', email='user1@test.com', password='Pass123!')
        user2 = User.objects.create_user(username='user2', email='user2@test.com', password='Pass123!')
        
        self.client1.force_authenticate(user=user1)
        self.client2.force_authenticate(user=user2)

        # Create group
        group = AppGroup.objects.create(name='Chat Group', created_by=user1)
        GroupMembership.objects.create(group=group, user=user1, role='admin', is_confirmed=True)
        GroupMembership.objects.create(group=group, user=user2, role='member', is_confirmed=True)

        # Create decision
        decision = Decision.objects.create(
            group=group,
            title='Test Decision',
            item_type='test',
            rules={'type': 'unanimous'},
            status='open'
        )

        # Get or create conversation
        response = self.client1.get(f'/api/v1/decisions/{decision.id}/conversation/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # User 1 sends message
        message_data_1 = {'text': 'Hello from user 1'}
        response = self.client1.post(f'/api/v1/decisions/{decision.id}/messages/', message_data_1, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # User 2 sends message
        message_data_2 = {'text': 'Hello from user 2'}
        response = self.client2.post(f'/api/v1/decisions/{decision.id}/messages/', message_data_2, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # User 1 retrieves messages
        response = self.client1.get(f'/api/v1/decisions/{decision.id}/messages/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Messages are in data.results
        messages = response.data.get('data', {}).get('results', [])
        self.assertEqual(len(messages), 2)

        # Verify chronological ordering
        self.assertEqual(messages[0]['text'], 'Hello from user 1')
        self.assertEqual(messages[1]['text'], 'Hello from user 2')
        self.assertLessEqual(messages[0]['sent_at'], messages[1]['sent_at'])

        # Verify sender information
        self.assertEqual(messages[0]['sender_username'], 'user1')
        self.assertEqual(messages[1]['sender_username'], 'user2')

    def test_filtering_and_search_combinations(self):
        """Test filtering and search with various tag and attribute combinations"""
        # Setup
        user = User.objects.create_user(username='organizer', email='org@test.com', password='Pass123!')
        self.client1.force_authenticate(user=user)

        group = AppGroup.objects.create(name='Filter Group', created_by=user)
        GroupMembership.objects.create(group=group, user=user, role='admin', is_confirmed=True)

        decision = Decision.objects.create(
            group=group,
            title='Filter Test',
            item_type='product',
            rules={'type': 'unanimous'},
            status='open'
        )

        # Create taxonomy and terms
        category_taxonomy = Taxonomy.objects.create(name='category', description='Product categories')
        electronics_term = Term.objects.create(taxonomy=category_taxonomy, value='electronics')
        furniture_term = Term.objects.create(taxonomy=category_taxonomy, value='furniture')

        # Create items with different attributes
        laptop = DecisionItem.objects.create(
            decision=decision,
            label='Laptop',
            attributes={'price': 1000, 'brand': 'Dell', 'color': 'black'}
        )
        DecisionItemTerm.objects.create(item=laptop, term=electronics_term)

        phone = DecisionItem.objects.create(
            decision=decision,
            label='Phone',
            attributes={'price': 800, 'brand': 'Apple', 'color': 'white'}
        )
        DecisionItemTerm.objects.create(item=phone, term=electronics_term)

        desk = DecisionItem.objects.create(
            decision=decision,
            label='Desk',
            attributes={'price': 500, 'brand': 'IKEA', 'color': 'brown'}
        )
        DecisionItemTerm.objects.create(item=desk, term=furniture_term)

        # Test 1: Filter by tag only
        response = self.client1.get(f'/api/v1/items/?decision_id={decision.id}&tag={electronics_term.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        items = response.data['data']['results']
        self.assertEqual(len(items), 2)
        labels = [item['label'] for item in items]
        self.assertIn('Laptop', labels)
        self.assertIn('Phone', labels)
        self.assertNotIn('Desk', labels)

        # Test 2: Filter by attribute only
        response = self.client1.get(f'/api/v1/items/?decision_id={decision.id}&price=500')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        items = response.data['data']['results']
        self.assertGreaterEqual(len(items), 1)  # Desk

        # Test 3: Combined filter (tag + attribute)
        response = self.client1.get(
            f'/api/v1/items/?decision_id={decision.id}&tag={electronics_term.id}&price=1000'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        items = response.data['data']['results']
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['label'], 'Laptop')

        # Test 4: Pagination
        response = self.client1.get(f'/api/v1/items/?decision_id={decision.id}&page_size=2&page=1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLessEqual(len(response.data['data']['results']), 2)

    def test_authorization_boundaries(self):
        """Test that non-members cannot access group resources"""
        # Setup: Create two users
        member_user = User.objects.create_user(
            username='member', 
            email='member@test.com', 
            password='Pass123!'
        )
        non_member_user = User.objects.create_user(
            username='nonmember', 
            email='nonmember@test.com', 
            password='Pass123!'
        )

        self.client1.force_authenticate(user=member_user)
        self.client_non_member.force_authenticate(user=non_member_user)

        # Create group with member
        group = AppGroup.objects.create(name='Private Group', created_by=member_user)
        GroupMembership.objects.create(
            group=group, 
            user=member_user, 
            role='admin', 
            is_confirmed=True
        )

        # Create decision
        decision = Decision.objects.create(
            group=group,
            title='Private Decision',
            item_type='test',
            rules={'type': 'unanimous'},
            status='open'
        )

        # Create item
        item = DecisionItem.objects.create(
            decision=decision,
            label='Test Item',
            attributes={}
        )

        # Test 1: Non-member cannot access group details
        response = self.client_non_member.get(f'/api/v1/groups/{group.id}/')
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

        # Test 2: Non-member cannot access decision
        response = self.client_non_member.get(f'/api/v1/decisions/{decision.id}/')
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

        # Test 3: Non-member cannot vote
        response = self.client_non_member.post(
            f'/api/v1/votes/items/{item.id}/votes/', 
            {'is_like': True},
            format='json'
        )
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

        # Test 4: Non-member cannot access chat
        response = self.client_non_member.get(f'/api/v1/decisions/{decision.id}/conversation/')
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

        # Test 5: Non-member cannot send messages
        response = self.client_non_member.post(
            f'/api/v1/decisions/{decision.id}/messages/',
            {'text': 'Unauthorized message'},
            format='json'
        )
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

        # Test 6: Member CAN access all resources
        response = self.client1.get(f'/api/v1/groups/{group.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client1.get(f'/api/v1/decisions/{decision.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client1.post(f'/api/v1/votes/items/{item.id}/votes/', {'is_like': True}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_unanimous_approval_rule(self):
        """Test that unanimous approval rule works correctly"""
        # Setup
        user1 = User.objects.create_user(username='u1', email='u1@test.com', password='Pass123!')
        user2 = User.objects.create_user(username='u2', email='u2@test.com', password='Pass123!')
        user3 = User.objects.create_user(username='u3', email='u3@test.com', password='Pass123!')

        group = AppGroup.objects.create(name='Unanimous Group', created_by=user1)
        GroupMembership.objects.create(group=group, user=user1, role='admin', is_confirmed=True)
        GroupMembership.objects.create(group=group, user=user2, role='member', is_confirmed=True)
        GroupMembership.objects.create(group=group, user=user3, role='member', is_confirmed=True)

        decision = Decision.objects.create(
            group=group,
            title='Unanimous Test',
            item_type='test',
            rules={'type': 'unanimous'},
            status='open'
        )

        item = DecisionItem.objects.create(
            decision=decision,
            label='Test Item',
            attributes={}
        )

        # Vote 1: Not yet unanimous
        DecisionVote.objects.create(item=item, user=user1, is_like=True)
        self.assertEqual(DecisionSelection.objects.filter(item=item).count(), 0)

        # Vote 2: Still not unanimous
        DecisionVote.objects.create(item=item, user=user2, is_like=True)
        self.assertEqual(DecisionSelection.objects.filter(item=item).count(), 0)

        # Vote 3: Now unanimous - should create selection
        DecisionVote.objects.create(item=item, user=user3, is_like=True)
        
        # Check if selection was created by trigger
        selections = DecisionSelection.objects.filter(item=item)
        self.assertEqual(selections.count(), 1)
        self.assertIsNotNone(selections.first().snapshot)
