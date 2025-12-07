"""
Integration tests for taxonomy endpoints.
"""

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from core.models import UserAccount, Taxonomy, Term


class TaxonomyEndpointTests(TestCase):
    """Test taxonomy API endpoints"""
    
    def setUp(self):
        """Set up test client and user"""
        self.client = APIClient()
        
        # Create a test user
        self.user = UserAccount.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        
        # Authenticate the client
        self.client.force_authenticate(user=self.user)
    
    def test_create_taxonomy(self):
        """Test creating a taxonomy via POST /api/v1/taxonomies"""
        data = {
            'name': 'category',
            'description': 'Item categories'
        }
        
        response = self.client.post('/api/v1/taxonomies/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['data']['name'], 'category')
        
        # Verify taxonomy was created in database
        taxonomy = Taxonomy.objects.get(name='category')
        self.assertEqual(taxonomy.description, 'Item categories')
    
    def test_list_taxonomies(self):
        """Test listing taxonomies via GET /api/v1/taxonomies"""
        # Create some taxonomies
        Taxonomy.objects.create(name='category', description='Categories')
        Taxonomy.objects.create(name='origin', description='Origins')
        
        response = self.client.get('/api/v1/taxonomies/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(len(response.data['data']), 2)
    
    def test_retrieve_taxonomy(self):
        """Test retrieving a taxonomy via GET /api/v1/taxonomies/:id"""
        taxonomy = Taxonomy.objects.create(name='category', description='Categories')
        
        response = self.client.get(f'/api/v1/taxonomies/{taxonomy.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['data']['name'], 'category')
    
    def test_add_term_to_taxonomy(self):
        """Test adding a term via POST /api/v1/taxonomies/:id/terms"""
        taxonomy = Taxonomy.objects.create(name='category', description='Categories')
        
        data = {
            'value': 'SUV',
            'attributes': {
                'color': '#FF0000',
                'icon': 'car'
            }
        }
        
        response = self.client.post(f'/api/v1/taxonomies/{taxonomy.id}/terms/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['data']['value'], 'SUV')
        self.assertEqual(response.data['data']['attributes']['color'], '#FF0000')
        
        # Verify term was created in database
        term = Term.objects.get(taxonomy=taxonomy, value='SUV')
        self.assertEqual(term.attributes['icon'], 'car')
    
    def test_list_terms_in_taxonomy(self):
        """Test listing terms via GET /api/v1/taxonomies/:id/terms"""
        taxonomy = Taxonomy.objects.create(name='category', description='Categories')
        Term.objects.create(taxonomy=taxonomy, value='SUV')
        Term.objects.create(taxonomy=taxonomy, value='Sedan')
        
        response = self.client.get(f'/api/v1/taxonomies/{taxonomy.id}/terms/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(len(response.data['data']), 2)
    
    def test_taxonomy_name_uniqueness_validation(self):
        """Test that duplicate taxonomy names are rejected"""
        Taxonomy.objects.create(name='category', description='First')
        
        data = {
            'name': 'category',
            'description': 'Second'
        }
        
        response = self.client.post('/api/v1/taxonomies/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], 'error')
        self.assertIn('name', response.data['errors'])
    
    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated users cannot access taxonomy endpoints"""
        # Create an unauthenticated client
        client = APIClient()
        
        response = client.get('/api/v1/taxonomies/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
