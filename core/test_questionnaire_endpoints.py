"""
Endpoint tests for Questionnaire module
"""

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from core.models import UserAccount, AppGroup, GroupMembership, Decision, Question, AnswerOption, UserAnswer


class QuestionnaireEndpointTests(TestCase):
    """Test questionnaire endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create test user
        self.user = UserAccount.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Authenticate
        self.client.force_authenticate(user=self.user)
        
        # Create test group
        self.group = AppGroup.objects.create(
            name='Test Group',
            description='Test',
            created_by=self.user
        )
        
        GroupMembership.objects.create(
            group=self.group,
            user=self.user,
            role='admin',
            is_confirmed=True,
            confirmed_at=timezone.now()
        )
        
        # Create test decision
        self.decision = Decision.objects.create(
            group=self.group,
            title='Test Decision',
            description='Test',
            item_type='car',
            rules={'type': 'unanimous'},
            status='open'
        )
        
        # Create test questions
        self.global_question = Question.objects.create(
            text='What is your favorite color?',
            scope='global'
        )
        
        self.item_type_question = Question.objects.create(
            text='What type of car do you prefer?',
            scope='item_type',
            item_type='car'
        )
        
        self.decision_question = Question.objects.create(
            text='How important is this decision to you?',
            scope='decision'
        )
        
        # Create answer options
        self.option1 = AnswerOption.objects.create(
            question=self.global_question,
            text='Red',
            order_num=1
        )
        
        self.option2 = AnswerOption.objects.create(
            question=self.global_question,
            text='Blue',
            order_num=2
        )
    
    def test_list_questions(self):
        """Test listing all questions"""
        response = self.client.get('/api/v1/questions/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(len(response.data['data']), 3)
    
    def test_list_questions_by_scope(self):
        """Test filtering questions by scope"""
        response = self.client.get('/api/v1/questions/?scope=global')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['text'], 'What is your favorite color?')
    
    def test_list_questions_by_item_type(self):
        """Test filtering questions by item_type"""
        response = self.client.get('/api/v1/questions/?item_type=car')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['text'], 'What type of car do you prefer?')
    
    def test_submit_answer_with_option(self):
        """Test submitting an answer with answer_option"""
        data = {
            'question': str(self.global_question.id),
            'answer_option': str(self.option1.id)
        }
        
        response = self.client.post('/api/v1/answers/submit/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(str(response.data['data']['question']), str(self.global_question.id))
        self.assertEqual(str(response.data['data']['answer_option']), str(self.option1.id))
        
        # Verify answer was created
        answer = UserAnswer.objects.get(user=self.user, question=self.global_question)
        self.assertEqual(answer.answer_option, self.option1)
    
    def test_submit_answer_with_value(self):
        """Test submitting an answer with answer_value"""
        data = {
            'question': str(self.decision_question.id),
            'decision': str(self.decision.id),
            'answer_value': {'rating': 5, 'text': 'Very important'}
        }
        
        response = self.client.post('/api/v1/answers/submit/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['data']['answer_value']['rating'], 5)
        
        # Verify answer was created
        answer = UserAnswer.objects.get(
            user=self.user,
            question=self.decision_question,
            decision=self.decision
        )
        self.assertEqual(answer.answer_value['rating'], 5)
    
    def test_update_existing_answer(self):
        """Test updating an existing answer"""
        # Create initial answer
        UserAnswer.objects.create(
            user=self.user,
            question=self.global_question,
            answer_option=self.option1
        )
        
        # Submit new answer for same question (should update)
        data = {
            'question': str(self.global_question.id),
            'answer_option': str(self.option2.id)
        }
        
        response = self.client.post('/api/v1/answers/submit/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(str(response.data['data']['answer_option']), str(self.option2.id))
        
        # Verify only one answer exists and it was updated
        answers = UserAnswer.objects.filter(user=self.user, question=self.global_question)
        self.assertEqual(answers.count(), 1)
        self.assertEqual(answers.first().answer_option, self.option2)
    
    def test_get_my_answers(self):
        """Test getting current user's answers"""
        # Create some answers
        UserAnswer.objects.create(
            user=self.user,
            question=self.global_question,
            answer_option=self.option1
        )
        
        UserAnswer.objects.create(
            user=self.user,
            question=self.decision_question,
            decision=self.decision,
            answer_value={'rating': 5}
        )
        
        response = self.client.get('/api/v1/answers/my-answers/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(len(response.data['data']), 2)
    
    def test_get_my_answers_filtered_by_question(self):
        """Test filtering user's answers by question"""
        # Create some answers
        UserAnswer.objects.create(
            user=self.user,
            question=self.global_question,
            answer_option=self.option1
        )
        
        UserAnswer.objects.create(
            user=self.user,
            question=self.decision_question,
            decision=self.decision,
            answer_value={'rating': 5}
        )
        
        response = self.client.get(f'/api/v1/answers/my-answers/?question={self.global_question.id}')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(str(response.data['data'][0]['question']), str(self.global_question.id))
    
    def test_submit_answer_requires_authentication(self):
        """Test that submitting an answer requires authentication"""
        self.client.force_authenticate(user=None)
        
        data = {
            'question': str(self.global_question.id),
            'answer_option': str(self.option1.id)
        }
        
        response = self.client.post('/api/v1/answers/submit/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_submit_answer_without_option_or_value_fails(self):
        """Test that submitting an answer without option or value fails"""
        data = {
            'question': str(self.global_question.id)
        }
        
        response = self.client.post('/api/v1/answers/submit/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], 'error')
