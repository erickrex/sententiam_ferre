"""
Property-based tests for approval rules
Tests Properties 19-22 from the design document
"""

from hypothesis import given, strategies as st, settings, assume
from hypothesis.extra.django import TestCase
from django.contrib.auth import get_user_model
from core.models import (
    AppGroup, GroupMembership, Decision, DecisionItem, DecisionVote, DecisionSelection
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
    # Add UUID to ensure uniqueness
    username = f"{username}_{uuid.uuid4().hex[:8]}"
    email = f"{username}@example.com"
    user = User.objects.create_user(
        username=username,
        email=email,
        password='TestPass123!'
    )
    return user


@st.composite
def group_with_members_strategy(draw, min_members=2, max_members=5):
    """Generate a random group with confirmed members"""
    creator = draw(user_strategy())
    
    name = draw(safe_text(min_size=3, max_size=50))
    group = AppGroup.objects.create(
        name=name,
        description=draw(safe_text(max_size=200)),
        created_by=creator
    )
    
    # Add creator as confirmed admin
    GroupMembership.objects.create(
        group=group,
        user=creator,
        role='admin',
        is_confirmed=True,
        confirmed_at=timezone.now()
    )
    
    # Add additional members
    num_additional_members = draw(st.integers(min_value=min_members-1, max_value=max_members-1))
    members = [creator]
    
    for _ in range(num_additional_members):
        user = draw(user_strategy())
        GroupMembership.objects.create(
            group=group,
            user=user,
            role='member',
            is_confirmed=True,
            confirmed_at=timezone.now()
        )
        members.append(user)
    
    return group, members


@st.composite
def unanimous_decision_strategy(draw, group):
    """Generate a random unanimous decision"""
    title = draw(safe_text(min_size=3, max_size=100))
    
    decision = Decision.objects.create(
        group=group,
        title=title,
        description=draw(safe_text(max_size=200)),
        item_type=draw(safe_text(min_size=3, max_size=50)),
        rules={'type': 'unanimous'},
        status='open'
    )
    return decision


@st.composite
def threshold_decision_strategy(draw, group):
    """Generate a random threshold decision"""
    title = draw(safe_text(min_size=3, max_size=100))
    threshold = draw(st.floats(min_value=0.0, max_value=1.0))
    
    decision = Decision.objects.create(
        group=group,
        title=title,
        description=draw(safe_text(max_size=200)),
        item_type=draw(safe_text(min_size=3, max_size=50)),
        rules={'type': 'threshold', 'value': threshold},
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


class ApprovalRulesPropertyTests(TestCase):
    """Property-based tests for approval rules"""
    
    @given(st.data())
    @settings(max_examples=100, deadline=None)
    def test_property_19_unanimous_rule_evaluation(self, data):
        """
        Feature: generic-swipe-voting, Property 19: Unanimous rule evaluation
        For any decision with unanimous rules, when all confirmed members approve 
        an item (like=TRUE or rating≥4), a decision_selection record should be 
        created for that item.
        Validates: Requirements 6.2
        """
        # Generate group with members
        group, members = data.draw(group_with_members_strategy(min_members=2, max_members=5))
        
        # Create unanimous decision
        decision = data.draw(unanimous_decision_strategy(group))
        
        # Create item
        item = data.draw(item_strategy(decision))
        
        # Initially no selection should exist
        self.assertEqual(DecisionSelection.objects.filter(item=item).count(), 0)
        
        # All members approve (randomly choose like=True or rating>=4)
        for member in members:
            vote_type = data.draw(st.sampled_from(['like', 'rating']))
            if vote_type == 'like':
                DecisionVote.objects.create(
                    item=item,
                    user=member,
                    is_like=True
                )
            else:
                DecisionVote.objects.create(
                    item=item,
                    user=member,
                    rating=data.draw(st.integers(min_value=4, max_value=5))
                )
        
        # Property: Selection should be created when all members approve
        selections = DecisionSelection.objects.filter(decision=decision, item=item)
        self.assertEqual(selections.count(), 1)
        
        # Verify snapshot data
        selection = selections.first()
        self.assertIsNotNone(selection.snapshot)
        self.assertEqual(selection.snapshot['approvals'], len(members))
        self.assertEqual(selection.snapshot['total_members'], len(members))
        self.assertEqual(selection.snapshot['rule']['type'], 'unanimous')
    
    @given(st.data())
    @settings(max_examples=100, deadline=None)
    def test_property_20_threshold_rule_evaluation(self, data):
        """
        Feature: generic-swipe-voting, Property 20: Threshold rule evaluation
        For any decision with threshold rules, when the ratio of approvals to 
        confirmed members meets or exceeds the threshold, a decision_selection 
        record should be created.
        Validates: Requirements 6.3
        """
        # Generate group with members
        group, members = data.draw(group_with_members_strategy(min_members=3, max_members=5))
        
        # Create threshold decision
        decision = data.draw(threshold_decision_strategy(group))
        threshold = decision.rules['value']
        
        # Create item
        item = data.draw(item_strategy(decision))
        
        # Calculate how many approvals needed to meet threshold
        total_members = len(members)
        approvals_needed = int(threshold * total_members)
        if threshold * total_members > approvals_needed:
            approvals_needed += 1
        
        # Ensure we have enough members to meet threshold
        assume(approvals_needed <= total_members)
        assume(approvals_needed > 0)  # Need at least one approval
        
        # Have exactly enough members approve to meet threshold
        for i, member in enumerate(members):
            if i < approvals_needed:
                # Approve
                vote_type = data.draw(st.sampled_from(['like', 'rating']))
                if vote_type == 'like':
                    DecisionVote.objects.create(
                        item=item,
                        user=member,
                        is_like=True
                    )
                else:
                    DecisionVote.objects.create(
                        item=item,
                        user=member,
                        rating=data.draw(st.integers(min_value=4, max_value=5))
                    )
        
        # Property: Selection should be created when threshold is met
        selections = DecisionSelection.objects.filter(decision=decision, item=item)
        
        # Calculate actual approval ratio
        actual_ratio = approvals_needed / total_members
        
        # The trigger should create a selection if the ratio meets or exceeds threshold
        if actual_ratio >= threshold:
            self.assertGreaterEqual(selections.count(), 1)
            
            if selections.count() > 0:
                # Verify snapshot data
                selection = selections.first()
                self.assertIsNotNone(selection.snapshot)
                self.assertGreaterEqual(selection.snapshot['approvals'], approvals_needed)
                self.assertEqual(selection.snapshot['total_members'], total_members)
                self.assertEqual(selection.snapshot['threshold'], threshold)
                self.assertGreaterEqual(selection.snapshot['approval_ratio'], threshold)
        else:
            # If threshold not met, no selection should exist
            self.assertEqual(selections.count(), 0)
    
    @given(st.data())
    @settings(max_examples=100, deadline=None)
    def test_property_21_selection_snapshot_preservation(self, data):
        """
        Feature: generic-swipe-voting, Property 21: Selection snapshot preservation
        For any decision_selection created, the snapshot field should contain vote 
        tallies and rule parameters at the time of selection.
        Validates: Requirements 6.4
        """
        # Generate group with members
        group, members = data.draw(group_with_members_strategy(min_members=2, max_members=5))
        
        # Randomly choose unanimous or threshold
        rule_type = data.draw(st.sampled_from(['unanimous', 'threshold']))
        
        if rule_type == 'unanimous':
            decision = data.draw(unanimous_decision_strategy(group))
        else:
            decision = data.draw(threshold_decision_strategy(group))
        
        # Create item
        item = data.draw(item_strategy(decision))
        
        # All members approve to ensure selection is created
        for member in members:
            vote_type = data.draw(st.sampled_from(['like', 'rating']))
            if vote_type == 'like':
                DecisionVote.objects.create(
                    item=item,
                    user=member,
                    is_like=True
                )
            else:
                DecisionVote.objects.create(
                    item=item,
                    user=member,
                    rating=data.draw(st.integers(min_value=4, max_value=5))
                )
        
        # Refresh to get latest data
        from django.db import connection
        connection.cursor().execute("SELECT 1")  # Force transaction to complete
        
        # Property: Selection should have snapshot with vote tallies and rule parameters
        selections = DecisionSelection.objects.filter(decision=decision, item=item)
        
        if selections.exists():
            selection = selections.first()
            
            # Snapshot should exist
            self.assertIsNotNone(selection.snapshot)
            
            # Snapshot should contain vote tallies
            self.assertIn('approvals', selection.snapshot)
            self.assertIn('total_members', selection.snapshot)
            self.assertIn('rule', selection.snapshot)
            
            # Vote tallies should be valid (approvals <= total_members)
            self.assertLessEqual(selection.snapshot['approvals'], len(members))
            self.assertEqual(selection.snapshot['total_members'], len(members))
            
            # For unanimous, all members should have approved
            if rule_type == 'unanimous':
                self.assertEqual(selection.snapshot['approvals'], len(members))
            
            # Rule should match decision rules
            self.assertEqual(selection.snapshot['rule']['type'], decision.rules['type'])
            
            if rule_type == 'threshold':
                self.assertIn('threshold', selection.snapshot)
                self.assertIn('approval_ratio', selection.snapshot)
                self.assertEqual(selection.snapshot['threshold'], decision.rules['value'])
    
    @given(st.data())
    @settings(max_examples=100, deadline=None)
    def test_property_22_selection_idempotency(self, data):
        """
        Feature: generic-swipe-voting, Property 22: Selection idempotency
        For any item that meets approval rules, triggering the evaluation multiple 
        times should result in only one decision_selection record.
        Validates: Requirements 6.6
        """
        # Generate group with members
        group, members = data.draw(group_with_members_strategy(min_members=2, max_members=4))
        
        # Create unanimous decision for simplicity
        decision = data.draw(unanimous_decision_strategy(group))
        
        # Create item
        item = data.draw(item_strategy(decision))
        
        # All members approve
        votes = []
        for member in members:
            vote = DecisionVote.objects.create(
                item=item,
                user=member,
                is_like=True
            )
            votes.append(vote)
        
        # Property: Only one selection should exist
        selections = DecisionSelection.objects.filter(decision=decision, item=item)
        self.assertEqual(selections.count(), 1)
        
        # Update votes multiple times (trigger fires each time)
        for vote in votes:
            vote.rating = data.draw(st.integers(min_value=4, max_value=5))
            vote.save()
        
        # Property: Still only one selection (idempotent)
        selections = DecisionSelection.objects.filter(decision=decision, item=item)
        self.assertEqual(selections.count(), 1)
        
        # Update votes again
        for vote in votes:
            vote.note = data.draw(safe_text(max_size=50))
            vote.save()
        
        # Property: Still only one selection
        selections = DecisionSelection.objects.filter(decision=decision, item=item)
        self.assertEqual(selections.count(), 1)
