"""
Property-based tests for item management
Tests Properties 13-16 from the design document
"""

from hypothesis import given, strategies as st, settings
from hypothesis.extra.django import TestCase
from django.contrib.auth import get_user_model
from core.models import (
    AppGroup, GroupMembership, Decision, DecisionItem, 
    CatalogItem, Taxonomy, Term, DecisionItemTerm
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
def attributes_strategy(draw):
    """Generate random JSONB attributes"""
    # Generate a dictionary with random keys and values
    num_attrs = draw(st.integers(min_value=0, max_value=5))
    attrs = {}
    for _ in range(num_attrs):
        key = draw(safe_text(min_size=1, max_size=20))
        value_type = draw(st.sampled_from(['string', 'int', 'float', 'bool']))
        if value_type == 'string':
            value = draw(safe_text(max_size=50))
        elif value_type == 'int':
            value = draw(st.integers(min_value=0, max_value=10000))
        elif value_type == 'float':
            value = draw(st.floats(min_value=0.0, max_value=10000.0, allow_nan=False, allow_infinity=False))
        else:
            value = draw(st.booleans())
        attrs[key] = value
    return attrs if attrs else None


@st.composite
def catalog_item_strategy(draw):
    """Generate a random catalog item"""
    label = draw(safe_text(min_size=3, max_size=100))
    attributes = draw(attributes_strategy())
    
    catalog_item = CatalogItem.objects.create(
        label=label,
        attributes=attributes
    )
    return catalog_item


@st.composite
def taxonomy_strategy(draw):
    """Generate a random taxonomy"""
    name = draw(safe_text(min_size=3, max_size=50))
    # Ensure uniqueness
    name = f"{name}_{uuid.uuid4().hex[:8]}"
    
    taxonomy = Taxonomy.objects.create(
        name=name,
        description=draw(safe_text(max_size=200))
    )
    return taxonomy


@st.composite
def term_strategy(draw, taxonomy):
    """Generate a random term for a taxonomy"""
    value = draw(safe_text(min_size=1, max_size=50))
    
    term = Term.objects.create(
        taxonomy=taxonomy,
        value=value,
        attributes=draw(attributes_strategy())
    )
    return term


class ItemManagementPropertyTests(TestCase):
    """Property-based tests for item management"""
    
    @given(st.data())
    @settings(max_examples=100, deadline=None)
    def test_property_13_item_attribute_storage(self, data):
        """
        Feature: generic-swipe-voting, Property 13: Item attribute storage
        For any item with JSONB attributes, storing and retrieving the item 
        should preserve all attribute key-value pairs.
        Validates: Requirements 4.1
        """
        # Generate test data
        user = data.draw(user_strategy())
        group = data.draw(group_strategy(user))
        decision = data.draw(decision_strategy(group))
        
        # Generate item with attributes
        label = data.draw(safe_text(min_size=3, max_size=100))
        attributes = data.draw(attributes_strategy())
        
        # Create item
        item = DecisionItem.objects.create(
            decision=decision,
            label=label,
            attributes=attributes
        )
        
        # Retrieve item
        retrieved_item = DecisionItem.objects.get(id=item.id)
        
        # Property: All attribute key-value pairs should be preserved
        if attributes:
            self.assertEqual(retrieved_item.attributes, attributes)
            for key, value in attributes.items():
                self.assertIn(key, retrieved_item.attributes)
                self.assertEqual(retrieved_item.attributes[key], value)
        else:
            self.assertIsNone(retrieved_item.attributes)
    
    @given(st.data())
    @settings(max_examples=100, deadline=None)
    def test_property_14_catalog_item_linking(self, data):
        """
        Feature: generic-swipe-voting, Property 14: Catalog item linking
        For any item linked to a catalog_item, the catalog_item_id reference 
        should be stored and retrievable.
        Validates: Requirements 4.2
        """
        # Generate test data
        user = data.draw(user_strategy())
        group = data.draw(group_strategy(user))
        decision = data.draw(decision_strategy(group))
        catalog_item = data.draw(catalog_item_strategy())
        
        # Generate item linked to catalog item
        label = data.draw(safe_text(min_size=3, max_size=100))
        
        # Create item with catalog_item reference
        item = DecisionItem.objects.create(
            decision=decision,
            catalog_item=catalog_item,
            label=label,
            attributes=data.draw(attributes_strategy())
        )
        
        # Retrieve item
        retrieved_item = DecisionItem.objects.get(id=item.id)
        
        # Property: catalog_item_id reference should be stored and retrievable
        self.assertIsNotNone(retrieved_item.catalog_item)
        self.assertEqual(retrieved_item.catalog_item.id, catalog_item.id)
        self.assertEqual(retrieved_item.catalog_item.label, catalog_item.label)
    
    @given(st.data())
    @settings(max_examples=100, deadline=None)
    def test_property_15_item_tagging_creates_link(self, data):
        """
        Feature: generic-swipe-voting, Property 15: Item tagging creates link
        For any item and term, tagging the item should create a decision_item_term 
        record linking them.
        Validates: Requirements 4.3
        """
        # Generate test data
        user = data.draw(user_strategy())
        group = data.draw(group_strategy(user))
        decision = data.draw(decision_strategy(group))
        taxonomy = data.draw(taxonomy_strategy())
        term = data.draw(term_strategy(taxonomy))
        
        # Generate item
        label = data.draw(safe_text(min_size=3, max_size=100))
        
        item = DecisionItem.objects.create(
            decision=decision,
            label=label,
            attributes=data.draw(attributes_strategy())
        )
        
        # Tag the item
        item_term = DecisionItemTerm.objects.create(
            item=item,
            term=term
        )
        
        # Property: A decision_item_term record should exist linking item and term
        self.assertTrue(
            DecisionItemTerm.objects.filter(item=item, term=term).exists()
        )
        
        # Verify the link is retrievable
        retrieved_link = DecisionItemTerm.objects.get(id=item_term.id)
        self.assertEqual(retrieved_link.item.id, item.id)
        self.assertEqual(retrieved_link.term.id, term.id)
        
        # Verify we can access term through item
        item_terms = item.item_terms.all()
        self.assertIn(item_term, item_terms)
    
    @given(st.data())
    @settings(max_examples=100, deadline=None)
    def test_property_16_duplicate_item_prevention(self, data):
        """
        Feature: generic-swipe-voting, Property 16: Duplicate item prevention
        For any decision, attempting to add an item with the same external_ref 
        and label as an existing item should be rejected.
        Validates: Requirements 4.4
        """
        # Generate test data
        user = data.draw(user_strategy())
        group = data.draw(group_strategy(user))
        decision = data.draw(decision_strategy(group))
        
        # Generate item with external_ref
        label = data.draw(safe_text(min_size=3, max_size=100))
        external_ref = data.draw(safe_text(min_size=3, max_size=50))
        
        # Create first item
        item1 = DecisionItem.objects.create(
            decision=decision,
            label=label,
            external_ref=external_ref,
            attributes=data.draw(attributes_strategy())
        )
        
        # Property: Attempting to create duplicate should fail
        from django.db import IntegrityError, transaction
        
        # Use atomic block to handle the transaction properly
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                DecisionItem.objects.create(
                    decision=decision,
                    label=label,
                    external_ref=external_ref,
                    attributes=data.draw(attributes_strategy())
                )
        
        # Verify only one item exists with this combination
        items = DecisionItem.objects.filter(
            decision=decision,
            label=label,
            external_ref=external_ref
        )
        self.assertEqual(items.count(), 1)
        self.assertEqual(items.first().id, item1.id)
