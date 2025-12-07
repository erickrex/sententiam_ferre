"""
Property-based tests for dynamic threshold recalculation
Tests Property 45 from the design document
"""

from hypothesis import given, strategies as st, settings
from hypothesis.extra.django import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid
from core.models import (
    AppGroup, GroupMembership, Decision, DecisionItem, 
    DecisionVote, DecisionSelection
)

User = get_user_model()


class ThresholdRecalculationPropertyTests(TestCase):
    """Property-based tests for dynamic threshold recalculation"""
    
    def _create_test_fixtures(self, num_members=4):
        """Create test fixtures with specified number of members"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create users
        users = []
        for i in range(num_members):
            user = User.objects.create_user(
                username=f'testuser{i}_{unique_id}',
                email=f'test{i}_{unique_id}@example.com',
                password='TestPass123!'
            )
            users.append(user)
        
        # Create a test group
        group = AppGroup.objects.create(
            name=f'Test Group {unique_id}',
            description='Test group for threshold recalculation',
            created_by=users[0]
        )
        
        # Add all users as confirmed members
        memberships = []
        for i, user in enumerate(users):
            membership = GroupMembership.objects.create(
                group=group,
                user=user,
                role='admin' if i == 0 else 'member',
                is_confirmed=True,
                confirmed_at=timezone.now()
            )
            memberships.append(membership)
        
        return group, users, memberships
    
    @settings(max_examples=100, deadline=None)
    @given(
        threshold=st.floats(min_value=0.5, max_value=0.9),
        num_initial_members=st.integers(min_value=4, max_value=6),
        num_approvals=st.integers(min_value=2, max_value=4)
    )
    def test_property_45_member_removal_threshold_recalculation(
        self, threshold, num_initial_members, num_approvals
    ):
        """
        Feature: generic-swipe-voting, Property 45: Member removal threshold recalculation
        
        For any threshold-based decision, when a confirmed member leaves the group, 
        future threshold calculations should use the updated member count.
        Validates: Requirements 14.2
        """
        # Ensure num_approvals doesn't exceed num_initial_members
        num_approvals = min(num_approvals, num_initial_members)
        
        # Create test fixtures
        group, users, memberships = self._create_test_fixtures(num_initial_members)
        
        # Create a decision with threshold rules
        decision = Decision.objects.create(
            group=group,
            title='Test Decision',
            description='Test decision for threshold recalculation',
            item_type='test',
            rules={'type': 'threshold', 'value': threshold},
            status='open'
        )
        
        # Create an item
        item = DecisionItem.objects.create(
            decision=decision,
            label='Test Item',
            attributes={}
        )
        
        # Have some users vote in favor
        for i in range(num_approvals):
            DecisionVote.objects.create(
                item=item,
                user=users[i],
                is_like=True
            )
        
        # Calculate if item should be selected with initial member count
        initial_member_count = num_initial_members
        initial_approval_ratio = num_approvals / initial_member_count
        should_be_selected_initially = initial_approval_ratio >= threshold
        
        # Check if item was selected
        initial_selection = DecisionSelection.objects.filter(
            decision=decision,
            item=item
        ).first()
        
        if should_be_selected_initially:
            # Item should have been selected
            self.assertIsNotNone(
                initial_selection,
                f"Item should be selected: {num_approvals}/{initial_member_count} = "
                f"{initial_approval_ratio:.2f} >= {threshold:.2f}"
            )
        
        # Remove a member who didn't vote (if possible)
        member_to_remove = None
        for i in range(num_approvals, num_initial_members):
            if i < len(memberships):
                member_to_remove = memberships[i]
                break
        
        if member_to_remove:
            # Remove the member
            member_to_remove.delete()
            
            # Calculate new member count
            new_member_count = GroupMembership.objects.filter(
                group=group,
                is_confirmed=True
            ).count()
            
            # Verify member count decreased
            self.assertEqual(new_member_count, initial_member_count - 1)
            
            # The property we're testing: future threshold calculations should use 
            # the new member count. This is handled by the database trigger which 
            # counts confirmed members at the time of evaluation.
            
            # Create a new item to test with the updated member count
            new_item = DecisionItem.objects.create(
                decision=decision,
                label='New Test Item',
                attributes={}
            )
            
            # Have the same number of users vote (excluding the removed member)
            votes_on_new_item = 0
            for i in range(num_approvals):
                if i < len(users) and users[i] != member_to_remove.user:
                    DecisionVote.objects.create(
                        item=new_item,
                        user=users[i],
                        is_like=True
                    )
                    votes_on_new_item += 1
            
            # Calculate if new item should be selected with updated member count
            new_approval_ratio = votes_on_new_item / new_member_count
            should_be_selected_after = new_approval_ratio >= threshold
            
            # Check if new item was selected
            new_selection = DecisionSelection.objects.filter(
                decision=decision,
                item=new_item
            ).first()
            
            if should_be_selected_after:
                # New item should be selected with updated threshold
                self.assertIsNotNone(
                    new_selection,
                    f"New item should be selected: {votes_on_new_item}/{new_member_count} = "
                    f"{new_approval_ratio:.2f} >= {threshold:.2f}"
                )
            else:
                # New item should not be selected
                self.assertIsNone(
                    new_selection,
                    f"New item should not be selected: {votes_on_new_item}/{new_member_count} = "
                    f"{new_approval_ratio:.2f} < {threshold:.2f}"
                )
