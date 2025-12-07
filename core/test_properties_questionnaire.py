"""
Property-based tests for Questionnaire module

These tests use Hypothesis to verify correctness properties across all valid inputs.
Each test runs a minimum of 100 iterations with randomly generated data.
"""

from hypothesis import given, strategies as st, settings
from hypothesis.extra.django import TestCase
from django.utils import timezone
from core.models import UserAccount, AppGroup, GroupMembership, Decision, Question, AnswerOption, UserAnswer


# Hypothesis strategies for generating test data
def safe_text(min_size=0, max_size=100):
    """Generate text without NUL characters or other problematic chars"""
    return st.text(
        alphabet=st.characters(
            blacklist_characters='\x00',
            blacklist_categories=('Cs', 'Cc')
        ),
        min_size=min_size,
        max_size=max_size
    )


@st.composite
def user_strategy(draw):
    """Generate a valid user"""
    import uuid as uuid_lib
    
    # Add UUID to ensure uniqueness
    unique_id = str(uuid_lib.uuid4())[:8]
    username = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), min_codepoint=65),
        min_size=3,
        max_size=12
    ))
    username = f"{username}_{unique_id}"
    email = f"{username.lower()}@example.com"
    password = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), min_codepoint=65),
        min_size=8,
        max_size=20
    ))
    
    user = UserAccount.objects.create_user(
        username=username,
        email=email,
        password=password
    )
    return user


@st.composite
def group_strategy(draw, user=None):
    """Generate a valid group"""
    if user is None:
        user = draw(user_strategy())
    
    name = draw(safe_text(min_size=1, max_size=100))
    description = draw(safe_text(min_size=0, max_size=500))
    
    group = AppGroup.objects.create(
        name=name,
        description=description,
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
def decision_strategy(draw, group=None):
    """Generate a valid decision"""
    if group is None:
        user = draw(user_strategy())
        group = draw(group_strategy(user=user))
    
    title = draw(safe_text(min_size=1, max_size=200))
    description = draw(safe_text(min_size=0, max_size=1000))
    item_type = draw(safe_text(min_size=1, max_size=50))
    rules = {'type': 'unanimous'}
    
    decision = Decision.objects.create(
        group=group,
        title=title,
        description=description,
        item_type=item_type,
        rules=rules,
        status='open'
    )
    
    return decision


@st.composite
def question_strategy(draw, scope=None, item_type=None):
    """Generate a valid question"""
    text = draw(safe_text(min_size=1, max_size=500))
    
    if scope is None:
        scope = draw(st.sampled_from(['global', 'item_type', 'decision', 'group']))
    
    # If scope is item_type, ensure item_type is provided
    if scope == 'item_type' and item_type is None:
        item_type = draw(safe_text(min_size=1, max_size=50))
    
    question = Question.objects.create(
        text=text,
        scope=scope,
        item_type=item_type
    )
    
    return question


class QuestionnairePropertyTests(TestCase):
    """Property-based tests for Questionnaire functionality"""
    
    @settings(max_examples=100, deadline=None)
    @given(
        scope=st.sampled_from(['global', 'item_type', 'decision', 'group']),
        item_type_filter=safe_text(min_size=1, max_size=50)
    )
    def test_property_32_scoped_question_filtering(self, scope, item_type_filter):
        """
        Feature: generic-swipe-voting, Property 32: Scoped question filtering
        
        For any decision-scoped question query with a decision_id, only questions 
        with matching scope and scope_key should be returned.
        
        Validates: Requirements 9.2
        """
        # Create questions with different scopes
        global_question = Question.objects.create(
            text="Global question",
            scope='global'
        )
        
        item_type_question = Question.objects.create(
            text="Item type question",
            scope='item_type',
            item_type=item_type_filter
        )
        
        other_item_type_question = Question.objects.create(
            text="Other item type question",
            scope='item_type',
            item_type='other_type'
        )
        
        decision_question = Question.objects.create(
            text="Decision question",
            scope='decision'
        )
        
        group_question = Question.objects.create(
            text="Group question",
            scope='group'
        )
        
        # Test filtering by scope
        if scope == 'global':
            filtered = Question.objects.filter(scope='global')
            assert global_question in filtered
            assert decision_question not in filtered
            assert group_question not in filtered
        
        elif scope == 'item_type':
            # Filter by scope and item_type
            filtered = Question.objects.filter(scope='item_type', item_type=item_type_filter)
            assert item_type_question in filtered
            assert other_item_type_question not in filtered
            assert global_question not in filtered
        
        elif scope == 'decision':
            filtered = Question.objects.filter(scope='decision')
            assert decision_question in filtered
            assert global_question not in filtered
            assert group_question not in filtered
        
        elif scope == 'group':
            filtered = Question.objects.filter(scope='group')
            assert group_question in filtered
            assert global_question not in filtered
            assert decision_question not in filtered
    
    @settings(max_examples=100, deadline=None)
    @given(
        user=user_strategy(),
        answer_text=safe_text(min_size=1, max_size=500)
    )
    def test_property_33_answer_persistence(self, user, answer_text):
        """
        Feature: generic-swipe-voting, Property 33: Answer persistence
        
        For any answer submission, the user_answer should be stored with correct 
        question_id and optional decision_id references.
        
        Validates: Requirements 9.3
        """
        # Create a question
        question = Question.objects.create(
            text="Test question",
            scope='global'
        )
        
        # Create an answer option
        answer_option = AnswerOption.objects.create(
            question=question,
            text=answer_text,
            order_num=1
        )
        
        # Submit answer with answer_option
        answer1 = UserAnswer.objects.create(
            user=user,
            question=question,
            answer_option=answer_option
        )
        
        # Retrieve and verify
        retrieved1 = UserAnswer.objects.get(id=answer1.id)
        assert retrieved1.user == user
        assert retrieved1.question == question
        assert retrieved1.answer_option == answer_option
        assert retrieved1.decision is None
        
        # Create a decision and submit answer with decision_id
        group = AppGroup.objects.create(
            name="Test Group",
            description="Test",
            created_by=user
        )
        GroupMembership.objects.create(
            group=group,
            user=user,
            role='admin',
            is_confirmed=True,
            confirmed_at=timezone.now()
        )
        
        decision = Decision.objects.create(
            group=group,
            title="Test Decision",
            description="Test",
            rules={'type': 'unanimous'},
            status='open'
        )
        
        # Create decision-scoped question
        decision_question = Question.objects.create(
            text="Decision question",
            scope='decision'
        )
        
        # Submit answer with decision_id and answer_value
        answer_value = {"text": answer_text, "rating": 5}
        answer2 = UserAnswer.objects.create(
            user=user,
            question=decision_question,
            decision=decision,
            answer_value=answer_value
        )
        
        # Retrieve and verify
        retrieved2 = UserAnswer.objects.get(id=answer2.id)
        assert retrieved2.user == user
        assert retrieved2.question == decision_question
        assert retrieved2.decision == decision
        assert retrieved2.answer_value == answer_value
    
    @settings(max_examples=100, deadline=None)
    @given(
        user=user_strategy(),
        answer_text1=safe_text(min_size=1, max_size=100),
        answer_text2=safe_text(min_size=1, max_size=100)
    )
    def test_property_34_answer_uniqueness_enforcement(self, user, answer_text1, answer_text2):
        """
        Feature: generic-swipe-voting, Property 34: Answer uniqueness enforcement
        
        For any user, question, and decision combination, submitting multiple 
        answers should update the existing answer rather than create duplicates.
        
        Validates: Requirements 9.4
        """
        # Create a group and decision for testing
        group = AppGroup.objects.create(
            name="Test Group",
            description="Test",
            created_by=user
        )
        GroupMembership.objects.create(
            group=group,
            user=user,
            role='admin',
            is_confirmed=True,
            confirmed_at=timezone.now()
        )
        
        decision = Decision.objects.create(
            group=group,
            title="Test Decision",
            description="Test",
            rules={'type': 'unanimous'},
            status='open'
        )
        
        # Create a question
        question = Question.objects.create(
            text="Test question",
            scope='decision'
        )
        
        # Create answer options
        option1 = AnswerOption.objects.create(
            question=question,
            text=answer_text1,
            order_num=1
        )
        
        option2 = AnswerOption.objects.create(
            question=question,
            text=answer_text2,
            order_num=2
        )
        
        # Submit first answer with decision
        answer = UserAnswer.objects.create(
            user=user,
            question=question,
            decision=decision,
            answer_option=option1
        )
        
        # Verify only one answer exists
        assert UserAnswer.objects.filter(user=user, question=question, decision=decision).count() == 1
        
        # Try to submit another answer for the same question and decision (should fail due to unique constraint)
        from django.db import IntegrityError, transaction
        
        with transaction.atomic():
            try:
                UserAnswer.objects.create(
                    user=user,
                    question=question,
                    decision=decision,
                    answer_option=option2
                )
                # If we get here, the constraint didn't work
                assert False, "Should have raised IntegrityError"
            except IntegrityError:
                # Expected behavior - unique constraint prevents duplicate
                pass
        
        # Verify still only one answer exists
        assert UserAnswer.objects.filter(user=user, question=question, decision=decision).count() == 1
        
        # Update the existing answer (proper way to change answer)
        answer.answer_option = option2
        answer.save()
        
        # Verify the answer was updated
        retrieved = UserAnswer.objects.get(id=answer.id)
        assert retrieved.answer_option == option2
        
        # Verify still only one answer exists
        assert UserAnswer.objects.filter(user=user, question=question, decision=decision).count() == 1
        
        # Test that the same user can answer the same question for a different decision
        decision2 = Decision.objects.create(
            group=group,
            title="Test Decision 2",
            description="Test",
            rules={'type': 'unanimous'},
            status='open'
        )
        
        # This should succeed - different decision
        answer2 = UserAnswer.objects.create(
            user=user,
            question=question,
            decision=decision2,
            answer_option=option1
        )
        
        # Verify we now have two answers total (one per decision)
        assert UserAnswer.objects.filter(user=user, question=question).count() == 2
        assert UserAnswer.objects.filter(user=user, question=question, decision=decision).count() == 1
        assert UserAnswer.objects.filter(user=user, question=question, decision=decision2).count() == 1
