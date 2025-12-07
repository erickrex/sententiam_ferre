"""
Basic tests for voting endpoints
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from core.models import (
    AppGroup, GroupMembership, Decision, DecisionItem, DecisionVote
)
from django.utils import timezone

User = get_user_model()


class VoteEndpointTests(TestCase):
    """Tests for voting endpoints"""
    
    def setUp(self):
        """Set up test data"""
        # Create users
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='TestPass123!'
        )
        self.user2 = User.objects.create_user(
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
        
        # Create item
        self.item = DecisionItem.objects.create(
            decision=self.decision,
            label='Test Item',
            attributes={'test': 'value'}
        )
        
        # Set up API client
        self.client = APIClient()
    
    def test_cast_vote_like(self):
        """Test casting a like vote"""
        self.client.force_authenticate(user=self.user1)
        
        response = self.client.post(
            f'/api/v1/votes/items/{self.item.id}/votes/',
            {'is_like': True},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'success')
        self.assertTrue(response.data['data']['is_like'])
        
        # Verify vote was created
        vote = DecisionVote.objects.get(item=self.item, user=self.user1)
        self.assertTrue(vote.is_like)
        self.assertIsNone(vote.rating)
    
    def test_cast_vote_rating(self):
        """Test casting a rating vote"""
        self.client.force_authenticate(user=self.user1)
        
        response = self.client.post(
            f'/api/v1/votes/items/{self.item.id}/votes/',
            {'rating': 5},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['data']['rating'], 5)
        
        # Verify vote was created
        vote = DecisionVote.objects.get(item=self.item, user=self.user1)
        self.assertEqual(vote.rating, 5)
    
    def test_update_vote(self):
        """Test updating an existing vote"""
        self.client.force_authenticate(user=self.user1)
        
        # Create initial vote
        response = self.client.post(
            f'/api/v1/votes/items/{self.item.id}/votes/',
            {'is_like': True},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Update vote
        response = self.client.post(
            f'/api/v1/votes/items/{self.item.id}/votes/',
            {'is_like': False, 'rating': 2},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertFalse(response.data['data']['is_like'])
        self.assertEqual(response.data['data']['rating'], 2)
        
        # Verify only one vote exists
        votes = DecisionVote.objects.filter(item=self.item, user=self.user1)
        self.assertEqual(votes.count(), 1)
    
    def test_get_my_vote(self):
        """Test getting current user's vote"""
        self.client.force_authenticate(user=self.user1)
        
        # Create vote
        DecisionVote.objects.create(
            item=self.item,
            user=self.user1,
            is_like=True
        )
        
        # Get vote
        response = self.client.get(
            f'/api/v1/votes/items/{self.item.id}/votes/me/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertTrue(response.data['data']['is_like'])
    
    def test_get_my_vote_no_vote(self):
        """Test getting vote when user hasn't voted"""
        self.client.force_authenticate(user=self.user1)
        
        response = self.client.get(
            f'/api/v1/votes/items/{self.item.id}/votes/me/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertIsNone(response.data['data'])
    
    def test_get_vote_summary(self):
        """Test getting vote summary"""
        self.client.force_authenticate(user=self.user1)
        
        # Create votes
        DecisionVote.objects.create(
            item=self.item,
            user=self.user1,
            is_like=True,
            rating=5
        )
        DecisionVote.objects.create(
            item=self.item,
            user=self.user2,
            is_like=False,
            rating=2
        )
        
        # Get summary
        response = self.client.get(
            f'/api/v1/votes/items/{self.item.id}/votes/summary/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['data']['total_votes'], 2)
        self.assertEqual(response.data['data']['likes'], 1)
        self.assertEqual(response.data['data']['dislikes'], 1)
        self.assertEqual(response.data['data']['rating_count'], 2)
        self.assertEqual(response.data['data']['average_rating'], 3.5)
    
    def test_vote_on_closed_decision(self):
        """Test that voting on closed decision is prevented"""
        self.client.force_authenticate(user=self.user1)
        
        # Close the decision
        self.decision.status = 'closed'
        self.decision.save()
        
        # Try to vote
        response = self.client.post(
            f'/api/v1/votes/items/{self.item.id}/votes/',
            {'is_like': True},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], 'error')
    
    def test_vote_without_permission(self):
        """Test that non-members cannot vote"""
        # Create a user not in the group
        user3 = User.objects.create_user(
            username='user3',
            email='user3@example.com',
            password='TestPass123!'
        )
        
        self.client.force_authenticate(user=user3)
        
        response = self.client.post(
            f'/api/v1/votes/items/{self.item.id}/votes/',
            {'is_like': True},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['status'], 'error')
