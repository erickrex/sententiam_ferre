"""
Tests for database trigger functionality
Verifies that trg_maybe_select_item executes correctly
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from core.models import (
    AppGroup, GroupMembership, Decision, DecisionItem, DecisionVote, DecisionSelection
)
from django.utils import timezone

User = get_user_model()


class TriggerFunctionalityTests(TestCase):
    """Tests for database trigger functionality"""
    
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
        self.user3 = User.objects.create_user(
            username='user3',
            email='user3@example.com',
            password='TestPass123!'
        )
        
        # Create group
        self.group = AppGroup.objects.create(
            name='Test Group',
            description='Test Description',
            created_by=self.user1
        )
        
        # Add all users as confirmed members
        for user in [self.user1, self.user2, self.user3]:
            GroupMembership.objects.create(
                group=self.group,
                user=user,
                role='admin' if user == self.user1 else 'member',
                is_confirmed=True,
                confirmed_at=timezone.now()
            )
    
    def test_trigger_executes_on_vote_insert(self):
        """Test that trg_maybe_select_item executes on vote insert"""
        # Create unanimous decision
        decision = Decision.objects.create(
            group=self.group,
            title='Test Decision',
            description='Test Description',
            item_type='test',
            rules={'type': 'unanimous'},
            status='open'
        )
        
        # Create item
        item = DecisionItem.objects.create(
            decision=decision,
            label='Test Item',
            attributes={'test': 'value'}
        )
        
        # Initially no selection should exist
        self.assertEqual(DecisionSelection.objects.filter(item=item).count(), 0)
        
        # Add first vote (not unanimous yet)
        DecisionVote.objects.create(
            item=item,
            user=self.user1,
            is_like=True
        )
        
        # Still no selection (not all members voted)
        self.assertEqual(DecisionSelection.objects.filter(item=item).count(), 0)
        
        # Add second vote
        DecisionVote.objects.create(
            item=item,
            user=self.user2,
            is_like=True
        )
        
        # Still no selection (not all members voted)
        self.assertEqual(DecisionSelection.objects.filter(item=item).count(), 0)
        
        # Add third vote (now unanimous)
        DecisionVote.objects.create(
            item=item,
            user=self.user3,
            is_like=True
        )
        
        # Now selection should be created by trigger
        selections = DecisionSelection.objects.filter(item=item)
        self.assertEqual(selections.count(), 1)
        
        # Verify snapshot data
        selection = selections.first()
        self.assertIsNotNone(selection.snapshot)
        self.assertEqual(selection.snapshot['approvals'], 3)
        self.assertEqual(selection.snapshot['total_members'], 3)
        self.assertEqual(selection.snapshot['rule']['type'], 'unanimous')
    
    def test_trigger_creates_selection_for_unanimous_rules(self):
        """Test that trigger creates decision_selection for unanimous rules"""
        # Create unanimous decision
        decision = Decision.objects.create(
            group=self.group,
            title='Test Decision',
            description='Test Description',
            item_type='test',
            rules={'type': 'unanimous'},
            status='open'
        )
        
        # Create item
        item = DecisionItem.objects.create(
            decision=decision,
            label='Test Item',
            attributes={'test': 'value'}
        )
        
        # All users vote yes
        for user in [self.user1, self.user2, self.user3]:
            DecisionVote.objects.create(
                item=item,
                user=user,
                is_like=True
            )
        
        # Selection should be created
        selections = DecisionSelection.objects.filter(decision=decision, item=item)
        self.assertEqual(selections.count(), 1)
        
        selection = selections.first()
        self.assertEqual(selection.snapshot['approvals'], 3)
        self.assertEqual(selection.snapshot['total_members'], 3)
    
    def test_trigger_creates_selection_for_threshold_rules(self):
        """Test that trigger creates decision_selection for threshold rules"""
        # Create threshold decision (66% approval needed)
        decision = Decision.objects.create(
            group=self.group,
            title='Test Decision',
            description='Test Description',
            item_type='test',
            rules={'type': 'threshold', 'value': 0.66},
            status='open'
        )
        
        # Create item
        item = DecisionItem.objects.create(
            decision=decision,
            label='Test Item',
            attributes={'test': 'value'}
        )
        
        # Two users vote yes (66.67% approval)
        DecisionVote.objects.create(
            item=item,
            user=self.user1,
            is_like=True
        )
        DecisionVote.objects.create(
            item=item,
            user=self.user2,
            is_like=True
        )
        
        # Selection should be created (2/3 = 0.667 >= 0.66)
        selections = DecisionSelection.objects.filter(decision=decision, item=item)
        self.assertEqual(selections.count(), 1)
        
        selection = selections.first()
        self.assertEqual(selection.snapshot['approvals'], 2)
        self.assertEqual(selection.snapshot['total_members'], 3)
        self.assertEqual(selection.snapshot['threshold'], 0.66)
        self.assertGreaterEqual(selection.snapshot['approval_ratio'], 0.66)
    
    def test_trigger_respects_rating_threshold(self):
        """Test that trigger counts rating >= 4 as approval"""
        # Create unanimous decision
        decision = Decision.objects.create(
            group=self.group,
            title='Test Decision',
            description='Test Description',
            item_type='test',
            rules={'type': 'unanimous'},
            status='open'
        )
        
        # Create item
        item = DecisionItem.objects.create(
            decision=decision,
            label='Test Item',
            attributes={'test': 'value'}
        )
        
        # All users vote with rating >= 4
        DecisionVote.objects.create(
            item=item,
            user=self.user1,
            rating=4
        )
        DecisionVote.objects.create(
            item=item,
            user=self.user2,
            rating=5
        )
        DecisionVote.objects.create(
            item=item,
            user=self.user3,
            rating=4
        )
        
        # Selection should be created (all ratings >= 4)
        selections = DecisionSelection.objects.filter(decision=decision, item=item)
        self.assertEqual(selections.count(), 1)
    
    def test_trigger_does_not_create_duplicate_selections(self):
        """Test that trigger uses ON CONFLICT DO NOTHING for idempotency"""
        # Create unanimous decision
        decision = Decision.objects.create(
            group=self.group,
            title='Test Decision',
            description='Test Description',
            item_type='test',
            rules={'type': 'unanimous'},
            status='open'
        )
        
        # Create item
        item = DecisionItem.objects.create(
            decision=decision,
            label='Test Item',
            attributes={'test': 'value'}
        )
        
        # All users vote yes
        for user in [self.user1, self.user2, self.user3]:
            DecisionVote.objects.create(
                item=item,
                user=user,
                is_like=True
            )
        
        # Selection should be created
        self.assertEqual(DecisionSelection.objects.filter(item=item).count(), 1)
        
        # Update a vote (trigger fires again)
        vote = DecisionVote.objects.get(item=item, user=self.user1)
        vote.rating = 5
        vote.save()
        
        # Still only one selection (no duplicate)
        self.assertEqual(DecisionSelection.objects.filter(item=item).count(), 1)
    
    def test_trigger_handles_vote_updates(self):
        """Test that trigger executes on vote update"""
        # Create threshold decision (50% approval needed)
        decision = Decision.objects.create(
            group=self.group,
            title='Test Decision',
            description='Test Description',
            item_type='test',
            rules={'type': 'threshold', 'value': 0.5},
            status='open'
        )
        
        # Create item
        item = DecisionItem.objects.create(
            decision=decision,
            label='Test Item',
            attributes={'test': 'value'}
        )
        
        # One user votes no
        vote1 = DecisionVote.objects.create(
            item=item,
            user=self.user1,
            is_like=False
        )
        
        # No selection yet
        self.assertEqual(DecisionSelection.objects.filter(item=item).count(), 0)
        
        # Another user votes yes
        DecisionVote.objects.create(
            item=item,
            user=self.user2,
            is_like=True
        )
        
        # Still no selection (1/3 = 33% < 50%)
        self.assertEqual(DecisionSelection.objects.filter(item=item).count(), 0)
        
        # Update first vote to yes
        vote1.is_like = True
        vote1.save()
        
        # Now selection should be created (2/3 = 67% >= 50%)
        selections = DecisionSelection.objects.filter(item=item)
        self.assertEqual(selections.count(), 1)
