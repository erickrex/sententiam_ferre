"""
Unit tests for chat endpoints.
"""

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from core.models import (
    UserAccount, AppGroup, GroupMembership, Decision, 
    Conversation, Message
)


class ChatEndpointsTest(TestCase):
    """Test chat endpoints"""
    
    def setUp(self):
        """Set up test data"""
        # Create users
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
        
        # Create group
        self.group = AppGroup.objects.create(
            name='Test Group',
            description='Test Description',
            created_by=self.user1
        )
        
        # Add user1 as confirmed admin
        GroupMembership.objects.create(
            group=self.group,
            user=self.user1,
            role='admin',
            is_confirmed=True,
            confirmed_at=timezone.now()
        )
        
        # Add user2 as confirmed member
        GroupMembership.objects.create(
            group=self.group,
            user=self.user2,
            role='member',
            is_confirmed=True,
            confirmed_at=timezone.now()
        )
        
        # Create decision
        self.decision = Decision.objects.create(
            group=self.group,
            title='Test Decision',
            description='Test Description',
            item_type='test',
            rules={'type': 'unanimous'},
            status='open'
        )
        
        # Set up API client
        self.client = APIClient()
    
    def test_get_conversation(self):
        """Test getting or creating a conversation"""
        self.client.force_authenticate(user=self.user1)
        
        response = self.client.get(
            f'/api/v1/decisions/{self.decision.id}/conversation/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertIn('data', response.data)
        # UUID comparison - convert to string
        self.assertEqual(str(response.data['data']['decision']), str(self.decision.id))
        
        # Verify conversation was created
        conversation = Conversation.objects.filter(decision=self.decision).first()
        self.assertIsNotNone(conversation)
    
    def test_send_message(self):
        """Test sending a message"""
        self.client.force_authenticate(user=self.user1)
        
        response = self.client.post(
            f'/api/v1/decisions/{self.decision.id}/messages/',
            {'text': 'Hello, this is a test message!'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'success')
        self.assertIn('data', response.data)
        self.assertEqual(response.data['data']['text'], 'Hello, this is a test message!')
        self.assertEqual(response.data['data']['sender_username'], 'user1')
        
        # Verify message was created
        message = Message.objects.filter(
            conversation__decision=self.decision,
            sender=self.user1
        ).first()
        self.assertIsNotNone(message)
        self.assertEqual(message.text, 'Hello, this is a test message!')
    
    def test_list_messages(self):
        """Test listing messages"""
        # Create conversation and messages
        conversation = Conversation.objects.create(decision=self.decision)
        
        Message.objects.create(
            conversation=conversation,
            sender=self.user1,
            text='First message',
            is_read=False
        )
        
        Message.objects.create(
            conversation=conversation,
            sender=self.user2,
            text='Second message',
            is_read=False
        )
        
        self.client.force_authenticate(user=self.user1)
        
        response = self.client.get(
            f'/api/v1/decisions/{self.decision.id}/messages/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertIn('data', response.data)
        self.assertEqual(response.data['data']['count'], 2)
        self.assertEqual(len(response.data['data']['results']), 2)
        
        # Verify messages are ordered chronologically
        messages = response.data['data']['results']
        self.assertEqual(messages[0]['text'], 'First message')
        self.assertEqual(messages[1]['text'], 'Second message')
    
    def test_mark_message_read(self):
        """Test marking a message as read"""
        # Create conversation and message
        conversation = Conversation.objects.create(decision=self.decision)
        
        message = Message.objects.create(
            conversation=conversation,
            sender=self.user2,
            text='Test message',
            is_read=False
        )
        
        self.client.force_authenticate(user=self.user1)
        
        response = self.client.patch(
            f'/api/v1/messages/{message.id}/mark-read/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertIn('data', response.data)
        self.assertTrue(response.data['data']['is_read'])
        
        # Verify message was updated
        message.refresh_from_db()
        self.assertTrue(message.is_read)
    
    def test_non_member_cannot_access_conversation(self):
        """Test that non-members cannot access conversation"""
        # Create a user who is not a member
        non_member = UserAccount.objects.create_user(
            username='nonmember',
            email='nonmember@example.com',
            password='TestPass123!'
        )
        
        self.client.force_authenticate(user=non_member)
        
        response = self.client.get(
            f'/api/v1/decisions/{self.decision.id}/conversation/'
        )
        
        # Should return 404 because the decision is not in the user's queryset
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_non_member_cannot_send_message(self):
        """Test that non-members cannot send messages"""
        # Create a user who is not a member
        non_member = UserAccount.objects.create_user(
            username='nonmember',
            email='nonmember@example.com',
            password='TestPass123!'
        )
        
        self.client.force_authenticate(user=non_member)
        
        response = self.client.post(
            f'/api/v1/decisions/{self.decision.id}/messages/',
            {'text': 'This should not work'},
            format='json'
        )
        
        # Should return 404 because the decision is not in the user's queryset
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    
    def test_closed_decision_allows_read_access(self):
        """Test that closed decisions still allow reading messages"""
        # Create conversation and messages
        conversation = Conversation.objects.create(decision=self.decision)
        
        Message.objects.create(
            conversation=conversation,
            sender=self.user1,
            text='Message before closing',
            is_read=False
        )
        
        # Close the decision
        self.decision.status = 'closed'
        self.decision.save()
        
        self.client.force_authenticate(user=self.user1)
        
        # Should still be able to read messages
        response = self.client.get(
            f'/api/v1/decisions/{self.decision.id}/messages/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['data']['count'], 1)
