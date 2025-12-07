"""
Property-based tests for voting
Tests Properties 17-18 from the design document
"""

from hypothesis import given, strategies as st, settings
from hypothesis.extra.django import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from core.models import (
    AppGroup, GroupMembership, Decision, DecisionItem, DecisionVote
)
from django.utils import timezone
import uuid

User = get_user_model()


# Hypothesis strategies for generating test data
def safe_text(min_size=1, max_size=50):
    """Generate text without null characters"""
    return st.text(
        min_size=min_size, 
        max_size=max_size, 
        alphabet=st.characters(
            blacklist_characters='\x00',
            whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'), 
            min_codepoint=32, 
            max_codepoint=126
        )
    )


@st.composite
def user_strategy(draw):
    """Generate a random user"""
    username = draw(safe_text(min_size=3, max_size=20))
    email = f"{username}@example.com"
    user = User.objects.create_user(
        username=username,
        email=email,
        password='TestPass123!'
    )
    return user


@st.composite
def group_strategy(draw, user):
    """Generate a random group"""
    name = draw(safe_text(min_size=3, max_size=50))
    group = AppGroup.objects.create(
        name=name,
        description=draw(safe_text(max_size=200)),
        created_by=user
    )
    # Add creator as confirmed admin
    GroupMembership.objects.create(
        group=group,
        user=user,
        role='admin',
        is_confirmed=True,
        confirmed_at=timezone.now()
    )
    return group


@st.composite
def decision_strategy(draw, group):
    """Generate a random decision"""
    title = draw(safe_text(min_size=3, max_size=100))
    rule_type = draw(st.sampled_from(['unanimous', 'threshold']))
    
    if rule_type == 'unanimous':
        rules = {'type': 'unanimous'}
    else:
        rules = {'type': 'threshold', 'value': draw(st.floats(min_value=0.0, max_value=1.0))}
    
    decision = Decision.objects.create(
        group=group,
        title=title,
        description=draw(safe_text(max_size=200)),
        item_type=draw(safe_text(min_size=3, max_size=50)),
        rules=rules,
        status='open'
    )
    return decision


@st.composite
def item_strategy(draw, decision):
    """Generate a random decision item"""
    label = draw(safe_text(min_size=3, max_size=100))
    
    item = DecisionItem.objects.create(
        decision=decision,
        label=label,
        attributes=None
    )
    return item


@st.composite
def vote_data_strategy(draw):
    """Generate random vote data (is_like or rating or both)"""
    vote_type = draw(st.sampled_from(['like', 'rating', 'both']))
    
    if vote_type == 'like':
        return {
            'is_like': draw(st.booleans()),
            'rating': None
        }
    elif vote_type == 'rating':
        return {
            'is_like': None,
            'rating': draw(st.integers(min_value=1, max_value=5))
        }
    else:  # both
        return {
            'is_like': draw(st.booleans()),
            'rating': draw(st.integers(min_value=1, max_value=5))
        }


class VotingPropertyTests(TestCase):
    """Property-based tests for voting"""
    
    @given(st.data())
    @settings(max_examples=100, deadline=None)
    def test_property_17_vote_storage_and_updates(self, data):
        """
        Feature: generic-swipe-voting, Property 17: Vote storage and updates
        For any vote on an item, the system should store or update a single 
        decision_vote record with the provided is_like or rating values.
        Validates: Requirements 5.1, 5.2
        """
        # Generate test data
        user = data.draw(user_strategy())
        group = data.draw(group_strategy(user))
        decision = data.draw(decision_strategy(group))
        item = data.draw(item_strategy(decision))
        
        # Generate vote data
        vote_data = data.draw(vote_data_strategy())
        
        # Create initial vote
        vote = DecisionVote.objects.create(
            item=item,
            user=user,
            is_like=vote_data['is_like'],
            rating=vote_data['rating']
        )
        
        # Property: Vote should be stored with correct values
        retrieved_vote = DecisionVote.objects.get(id=vote.id)
        self.assertEqual(retrieved_vote.item.id, item.id)
        self.assertEqual(retrieved_vote.user.id, user.id)
        self.assertEqual(retrieved_vote.is_like, vote_data['is_like'])
        self.assertEqual(retrieved_vote.rating, vote_data['rating'])
        
        # Property: Only one vote per user-item combination
        vote_count = DecisionVote.objects.filter(user=user, item=item).count()
        self.assertEqual(vote_count, 1)
        
        # Test update: Generate new vote data
        new_vote_data = data.draw(vote_data_strategy())
        
        # Update the vote
        retrieved_vote.is_like = new_vote_data['is_like']
        retrieved_vote.rating = new_vote_data['rating']
        retrieved_vote.save()
        
        # Property: Still only one vote after update
        vote_count_after = DecisionVote.objects.filter(user=user, item=item).count()
        self.assertEqual(vote_count_after, 1)
        
        # Property: Updated values should be stored
        updated_vote = DecisionVote.objects.get(id=vote.id)
        self.assertEqual(updated_vote.is_like, new_vote_data['is_like'])
        self.assertEqual(updated_vote.rating, new_vote_data['rating'])
    
    @given(st.data())
    @settings(max_examples=100, deadline=None)
    def test_property_18_vote_field_requirement(self, data):
        """
        Feature: generic-swipe-voting, Property 18: Vote field requirement
        For any vote submission, at least one of is_like or rating must be provided, 
        otherwise the vote should be rejected.
        Validates: Requirements 5.4
        """
        # Generate test data
        user = data.draw(user_strategy())
        group = data.draw(group_strategy(user))
        decision = data.draw(decision_strategy(group))
        item = data.draw(item_strategy(decision))
        
        # Property: Vote with both is_like and rating as None should be rejected
        # The database constraint should prevent this
        with transaction.atomic():
            with self.assertRaises((IntegrityError, ValidationError)):
                vote = DecisionVote(
                    item=item,
                    user=user,
                    is_like=None,
                    rating=None
                )
                vote.full_clean()  # This should raise ValidationError
                vote.save()  # This should raise IntegrityError if full_clean is skipped
        
        # Verify no vote was created
        vote_count = DecisionVote.objects.filter(user=user, item=item).count()
        self.assertEqual(vote_count, 0)
        
        # Property: Vote with at least one field should succeed
        vote_data = data.draw(vote_data_strategy())
        
        vote = DecisionVote.objects.create(
            item=item,
            user=user,
            is_like=vote_data['is_like'],
            rating=vote_data['rating']
        )
        
        # Verify vote was created successfully
        self.assertIsNotNone(vote.id)
        retrieved_vote = DecisionVote.objects.get(id=vote.id)
        
        # At least one field should be non-None
        self.assertTrue(
            retrieved_vote.is_like is not None or retrieved_vote.rating is not None
        )
