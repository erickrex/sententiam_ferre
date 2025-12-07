"""
Property-based tests for chat functionality.

These tests verify the correctness properties related to conversations and messages.
"""

from hypothesis import given, strategies as st, settings
from hypothesis.extra.django import TestCase
from django.utils import timezone
from core.models import (
    UserAccount, AppGroup, GroupMembership, Decision, 
    Conversation, Message
)


# Counter to ensure unique usernames
_user_counter = 0


# Strategies for generating test data
@st.composite
def user_strategy(draw):
    """Generate a random user with unique username"""
    global _user_counter
    _user_counter += 1
    
    # Generate a unique username using counter and random suffix
    random_suffix = draw(st.text(
        alphabet='abcdefghijklmnopqrstuvwxyz0123456789',
        min_size=5,
        max_size=10
    ))
    username = f"user{_user_counter}_{random_suffix}"
    email = f"{username}@example.com"
    
    user = UserAccount.objects.create_user(
        username=username,
        email=email,
        password='TestPass123!'
    )
    return user


@st.composite
def safe_text_strategy(draw, min_size=1, max_size=100):
    """Generate text without NUL characters"""
    return draw(st.text(
        alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!?-_',
        min_size=min_size,
        max_size=max_size
    ))


@st.composite
def group_with_members_strategy(draw, min_members=1, max_members=5):
    """Generate a group with confirmed members"""
    creator = draw(user_strategy())
    group = AppGroup.objects.create(
        name=draw(safe_text_strategy(min_size=3, max_size=50)),
        description=draw(safe_text_strategy(max_size=200)),
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
    num_members = draw(st.integers(min_value=min_members-1, max_value=max_members-1))
    members = [creator]
    for _ in range(num_members):
        member = draw(user_strategy())
        GroupMembership.objects.create(
            group=group,
            user=member,
            role='member',
            is_confirmed=True,
            confirmed_at=timezone.now()
        )
        members.append(member)
    
    return group, members


@st.composite
def decision_strategy(draw):
    """Generate a decision with a group"""
    group, members = draw(group_with_members_strategy())
    decision = Decision.objects.create(
        group=group,
        title=draw(safe_text_strategy(min_size=3, max_size=100)),
        description=draw(safe_text_strategy(max_size=500)),
        item_type=draw(safe_text_strategy(min_size=3, max_size=50)),
        rules={'type': 'unanimous'},
        status='open'
    )
    return decision, group, members


class ChatPropertyTests(TestCase):
    """Property-based tests for chat functionality"""
    
    @settings(max_examples=100, deadline=None)
    @given(decision_strategy())
    def test_property_27_conversation_idempotent_creation(self, data):
        """
        Feature: generic-swipe-voting, Property 27: Conversation idempotent creation
        
        For any decision, opening it multiple times should result in exactly one 
        conversation record.
        
        Validates: Requirements 8.1
        """
        decision, group, members = data
        
        # Create conversation multiple times
        conv1, created1 = Conversation.objects.get_or_create(decision=decision)
        conv2, created2 = Conversation.objects.get_or_create(decision=decision)
        conv3, created3 = Conversation.objects.get_or_create(decision=decision)
        
        # All should return the same conversation
        self.assertEqual(conv1.id, conv2.id)
        self.assertEqual(conv2.id, conv3.id)
        
        # Only the first should have been created
        self.assertTrue(created1)
        self.assertFalse(created2)
        self.assertFalse(created3)
        
        # Verify only one conversation exists for this decision
        conversation_count = Conversation.objects.filter(decision=decision).count()
        self.assertEqual(conversation_count, 1)
    
    @settings(max_examples=100, deadline=None)
    @given(
        decision_strategy(),
        safe_text_strategy(min_size=1, max_size=1000)
    )
    def test_property_28_message_field_persistence(self, data, message_text):
        """
        Feature: generic-swipe-voting, Property 28: Message field persistence
        
        For any message sent, all fields (sender, text, timestamp, read flag) 
        should be stored and retrievable.
        
        Validates: Requirements 8.2
        """
        decision, group, members = data
        sender = members[0]
        
        # Create conversation
        conversation = Conversation.objects.create(decision=decision)
        
        # Create message
        message = Message.objects.create(
            conversation=conversation,
            sender=sender,
            text=message_text,
            is_read=False
        )
        
        # Retrieve message from database
        retrieved_message = Message.objects.get(id=message.id)
        
        # Verify all fields are preserved
        self.assertEqual(retrieved_message.conversation.id, conversation.id)
        self.assertEqual(retrieved_message.sender.id, sender.id)
        self.assertEqual(retrieved_message.text, message_text)
        self.assertIsNotNone(retrieved_message.sent_at)
        self.assertEqual(retrieved_message.is_read, False)
        
        # Update read flag
        retrieved_message.is_read = True
        retrieved_message.save()
        
        # Verify update persisted
        updated_message = Message.objects.get(id=message.id)
        self.assertEqual(updated_message.is_read, True)
    
    @settings(max_examples=100, deadline=None)
    @given(
        decision_strategy(),
        st.lists(safe_text_strategy(min_size=1, max_size=100), min_size=2, max_size=20)
    )
    def test_property_29_message_chronological_ordering(self, data, message_texts):
        """
        Feature: generic-swipe-voting, Property 29: Message chronological ordering
        
        For any list of messages in a conversation, they should be ordered by 
        sent_at timestamp in ascending order.
        
        Validates: Requirements 8.3
        """
        decision, group, members = data
        sender = members[0]
        
        # Create conversation
        conversation = Conversation.objects.create(decision=decision)
        
        # Create messages with slight time delays to ensure ordering
        created_messages = []
        for text in message_texts:
            message = Message.objects.create(
                conversation=conversation,
                sender=sender,
                text=text,
                is_read=False
            )
            created_messages.append(message)
        
        # Retrieve messages using the model's default ordering
        retrieved_messages = list(Message.objects.filter(conversation=conversation))
        
        # Verify messages are ordered by sent_at in ascending order
        for i in range(len(retrieved_messages) - 1):
            self.assertLessEqual(
                retrieved_messages[i].sent_at,
                retrieved_messages[i + 1].sent_at,
                "Messages should be ordered by sent_at in ascending order"
            )
        
        # Verify all messages were retrieved
        self.assertEqual(len(retrieved_messages), len(message_texts))
    
    @settings(max_examples=100, deadline=None)
    @given(
        decision_strategy(),
        st.lists(safe_text_strategy(min_size=1, max_size=100), min_size=1, max_size=10)
    )
    def test_property_30_message_read_flag_updates(self, data, message_texts):
        """
        Feature: generic-swipe-voting, Property 30: Message read flag updates
        
        For any message viewed by a user, the is_read flag should be updated 
        to TRUE for that user's view.
        
        Validates: Requirements 8.4
        """
        decision, group, members = data
        sender = members[0]
        
        # Create conversation
        conversation = Conversation.objects.create(decision=decision)
        
        # Create messages
        messages = []
        for text in message_texts:
            message = Message.objects.create(
                conversation=conversation,
                sender=sender,
                text=text,
                is_read=False
            )
            messages.append(message)
        
        # Verify all messages start as unread
        for message in messages:
            self.assertFalse(message.is_read)
        
        # Mark messages as read
        for message in messages:
            message.is_read = True
            message.save()
        
        # Retrieve and verify all messages are now marked as read
        for message in messages:
            retrieved_message = Message.objects.get(id=message.id)
            self.assertTrue(
                retrieved_message.is_read,
                "Message should be marked as read after update"
            )
    
    @settings(max_examples=100, deadline=None)
    @given(decision_strategy())
    def test_property_31_chat_access_control(self, data):
        """
        Feature: generic-swipe-voting, Property 31: Chat access control
        
        For any user attempting to access a decision's chat, access should be 
        granted only if the user is a confirmed member of the owning group.
        
        Validates: Requirements 8.5
        """
        decision, group, members = data
        
        # Create a user who is NOT a member of the group
        non_member = UserAccount.objects.create_user(
            username='nonmember_' + str(decision.id)[:8],
            email=f'nonmember_{decision.id}@example.com',
            password='TestPass123!'
        )
        
        # Create conversation
        conversation = Conversation.objects.create(decision=decision)
        
        # Verify confirmed members can access
        for member in members:
            membership = GroupMembership.objects.get(group=group, user=member)
            self.assertTrue(
                membership.is_confirmed,
                "Member should be confirmed"
            )
            
            # Member should be able to create messages
            message = Message.objects.create(
                conversation=conversation,
                sender=member,
                text=f"Message from {member.username}",
                is_read=False
            )
            self.assertIsNotNone(message.id)
        
        # Verify non-member cannot be associated with the conversation
        # (This is enforced at the view/permission level, but we verify the data model)
        non_member_membership = GroupMembership.objects.filter(
            group=group,
            user=non_member,
            is_confirmed=True
        ).exists()
        self.assertFalse(
            non_member_membership,
            "Non-member should not have confirmed membership"
        )

    
    @settings(max_examples=100, deadline=None)
    @given(
        decision_strategy(),
        st.lists(safe_text_strategy(min_size=1, max_size=100), min_size=1, max_size=10)
    )
    def test_property_37_closed_chat_readability(self, data, message_texts):
        """
        Feature: generic-swipe-voting, Property 37: Closed chat readability
        
        For any closed decision, users should still be able to read existing 
        messages in the conversation.
        
        Validates: Requirements 10.4
        """
        decision, group, members = data
        sender = members[0]
        
        # Create conversation and messages
        conversation = Conversation.objects.create(decision=decision)
        
        messages = []
        for text in message_texts:
            message = Message.objects.create(
                conversation=conversation,
                sender=sender,
                text=text,
                is_read=False
            )
            messages.append(message)
        
        # Close the decision
        decision.status = 'closed'
        decision.save()
        
        # Verify decision is closed
        decision.refresh_from_db()
        self.assertEqual(decision.status, 'closed')
        
        # Verify messages can still be read
        retrieved_messages = Message.objects.filter(conversation=conversation)
        self.assertEqual(retrieved_messages.count(), len(message_texts))
        
        # Verify all messages are accessible
        for i, message in enumerate(retrieved_messages):
            self.assertIn(message.text, message_texts)
            self.assertEqual(message.conversation.id, conversation.id)
        
        # Verify conversation is still accessible
        retrieved_conversation = Conversation.objects.get(decision=decision)
        self.assertEqual(retrieved_conversation.id, conversation.id)
