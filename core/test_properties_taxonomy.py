"""
Property-based tests for taxonomy management using Hypothesis.

These tests verify universal properties that should hold across all valid inputs
for taxonomy and term functionality.
"""

from hypothesis import given, strategies as st, settings
from hypothesis.extra.django import TestCase
from core.models import Taxonomy, Term, DecisionItem, Decision, AppGroup, UserAccount, GroupMembership
from django.utils import timezone
from django.db import IntegrityError


# Counter to ensure unique taxonomy names
_taxonomy_counter = 0


# Custom strategies for generating test data
@st.composite
def taxonomy_name_strategy(draw):
    """Generate a valid unique taxonomy name"""
    global _taxonomy_counter
    _taxonomy_counter += 1
    
    # Generate a unique name using counter and random suffix
    random_suffix = draw(st.text(
        alphabet='abcdefghijklmnopqrstuvwxyz',
        min_size=3,
        max_size=10
    ))
    name = f"taxonomy{_taxonomy_counter}_{random_suffix}"
    return name


@st.composite
def term_value_strategy(draw):
    """Generate a valid term value"""
    value = draw(st.text(
        alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_',
        min_size=1,
        max_size=50
    ))
    return value


@st.composite
def term_attributes_strategy(draw):
    """Generate valid term attributes (JSONB)"""
    # Generate optional attributes like color and icon
    has_color = draw(st.booleans())
    has_icon = draw(st.booleans())
    
    attributes = {}
    if has_color:
        # Generate a hex color
        color = draw(st.text(
            alphabet='0123456789ABCDEF',
            min_size=6,
            max_size=6
        ))
        attributes['color'] = f"#{color}"
    
    if has_icon:
        icon = draw(st.text(
            alphabet='abcdefghijklmnopqrstuvwxyz',
            min_size=3,
            max_size=15
        ))
        attributes['icon'] = icon
    
    return attributes if attributes else None


class TaxonomyManagementPropertyTests(TestCase):
    """Property-based tests for taxonomy management"""
    
    @settings(max_examples=100)
    @given(st.data())
    def test_property_38_taxonomy_name_uniqueness(self, data):
        """
        Feature: generic-swipe-voting, Property 38: Taxonomy name uniqueness
        
        For any taxonomy, the name field should be unique across all taxonomies,
        preventing duplicate taxonomy names.
        
        Validates: Requirements 11.1
        """
        from django.db import transaction
        
        # Generate a unique taxonomy name
        taxonomy_name = data.draw(taxonomy_name_strategy())
        
        # Generate optional description
        description = data.draw(st.one_of(
            st.none(),
            st.text(
                alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!?',
                max_size=200
            )
        ))
        
        # Create the first taxonomy
        taxonomy1 = Taxonomy.objects.create(
            name=taxonomy_name,
            description=description
        )
        
        # Verify the taxonomy was created
        self.assertIsNotNone(taxonomy1.id)
        self.assertEqual(taxonomy1.name, taxonomy_name)
        
        # Attempt to create a second taxonomy with the same name
        # This should raise an IntegrityError due to unique constraint
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Taxonomy.objects.create(
                    name=taxonomy_name,
                    description="Different description"
                )
        
        # Verify only one taxonomy with this name exists
        taxonomy_count = Taxonomy.objects.filter(name=taxonomy_name).count()
        self.assertEqual(taxonomy_count, 1, "Only one taxonomy with this name should exist")
    
    @settings(max_examples=100)
    @given(st.data())
    def test_property_39_term_taxonomy_linking(self, data):
        """
        Feature: generic-swipe-voting, Property 39: Term taxonomy linking
        
        For any term added to a taxonomy, the term should be linked to that 
        taxonomy via taxonomy_id.
        
        Validates: Requirements 11.2
        """
        # Create a taxonomy
        taxonomy_name = data.draw(taxonomy_name_strategy())
        taxonomy = Taxonomy.objects.create(
            name=taxonomy_name,
            description="Test taxonomy"
        )
        
        # Generate a term value
        term_value = data.draw(term_value_strategy())
        
        # Generate optional attributes
        attributes = data.draw(term_attributes_strategy())
        
        # Create a term linked to the taxonomy
        term = Term.objects.create(
            taxonomy=taxonomy,
            value=term_value,
            attributes=attributes
        )
        
        # Verify the term is linked to the taxonomy
        self.assertIsNotNone(term.id)
        self.assertEqual(term.taxonomy, taxonomy, "Term should be linked to the taxonomy")
        self.assertEqual(term.taxonomy.id, taxonomy.id, "Term's taxonomy_id should match")
        self.assertEqual(term.value, term_value)
        
        # Verify the term can be retrieved through the taxonomy
        retrieved_term = taxonomy.terms.filter(id=term.id).first()
        self.assertIsNotNone(retrieved_term, "Term should be retrievable through taxonomy")
        self.assertEqual(retrieved_term.id, term.id)
    
    @settings(max_examples=100)
    @given(st.data())
    def test_property_40_term_metadata_storage(self, data):
        """
        Feature: generic-swipe-voting, Property 40: Term metadata storage
        
        For any term with UI metadata (color, icon), the attributes JSONB field 
        should preserve all metadata.
        
        Validates: Requirements 11.3
        """
        # Create a taxonomy
        taxonomy_name = data.draw(taxonomy_name_strategy())
        taxonomy = Taxonomy.objects.create(
            name=taxonomy_name,
            description="Test taxonomy"
        )
        
        # Generate a term value
        term_value = data.draw(term_value_strategy())
        
        # Generate attributes with metadata
        attributes = data.draw(term_attributes_strategy())
        
        # Create a term with attributes
        term = Term.objects.create(
            taxonomy=taxonomy,
            value=term_value,
            attributes=attributes
        )
        
        # Retrieve the term from database
        retrieved_term = Term.objects.get(id=term.id)
        
        # Verify attributes are preserved
        if attributes is None:
            self.assertIsNone(retrieved_term.attributes, "Null attributes should be preserved")
        else:
            self.assertIsNotNone(retrieved_term.attributes, "Attributes should not be None")
            self.assertEqual(retrieved_term.attributes, attributes, "All attributes should be preserved")
            
            # Verify specific metadata fields if present
            if 'color' in attributes:
                self.assertEqual(retrieved_term.attributes['color'], attributes['color'], "Color metadata should be preserved")
            
            if 'icon' in attributes:
                self.assertEqual(retrieved_term.attributes['icon'], attributes['icon'], "Icon metadata should be preserved")
    
    @settings(max_examples=100)
    @given(st.data())
    def test_property_41_taxonomy_reusability(self, data):
        """
        Feature: generic-swipe-voting, Property 41: Taxonomy reusability
        
        For any taxonomy and its terms, they should be usable across multiple 
        decisions and item types without duplication.
        
        Validates: Requirements 11.4
        """
        # Create a taxonomy
        taxonomy_name = data.draw(taxonomy_name_strategy())
        taxonomy = Taxonomy.objects.create(
            name=taxonomy_name,
            description="Reusable taxonomy"
        )
        
        # Create a term
        term_value = data.draw(term_value_strategy())
        term = Term.objects.create(
            taxonomy=taxonomy,
            value=term_value,
            attributes=None
        )
        
        # Create two different users and groups for different decisions
        user1 = UserAccount.objects.create_user(
            username=f"user1_{data.draw(st.integers(min_value=1, max_value=999999))}",
            email=f"user1_{data.draw(st.integers(min_value=1, max_value=999999))}@example.com",
            password="TestPass123!"
        )
        
        user2 = UserAccount.objects.create_user(
            username=f"user2_{data.draw(st.integers(min_value=1, max_value=999999))}",
            email=f"user2_{data.draw(st.integers(min_value=1, max_value=999999))}@example.com",
            password="TestPass123!"
        )
        
        group1 = AppGroup.objects.create(
            name=f"group1_{data.draw(st.integers(min_value=1, max_value=999999))}",
            created_by=user1
        )
        
        group2 = AppGroup.objects.create(
            name=f"group2_{data.draw(st.integers(min_value=1, max_value=999999))}",
            created_by=user2
        )
        
        # Create two decisions with different item types
        decision1 = Decision.objects.create(
            group=group1,
            title="Decision 1",
            item_type="cars",
            rules={"type": "unanimous"},
            status="open"
        )
        
        decision2 = Decision.objects.create(
            group=group2,
            title="Decision 2",
            item_type="restaurants",
            rules={"type": "threshold", "value": 0.7},
            status="open"
        )
        
        # Create items in both decisions
        item1 = DecisionItem.objects.create(
            decision=decision1,
            label="Item 1",
            attributes={"type": "car"}
        )
        
        item2 = DecisionItem.objects.create(
            decision=decision2,
            label="Item 2",
            attributes={"type": "restaurant"}
        )
        
        # Use the same term for both items (from different decisions and item types)
        from core.models import DecisionItemTerm
        
        item_term1 = DecisionItemTerm.objects.create(
            item=item1,
            term=term
        )
        
        item_term2 = DecisionItemTerm.objects.create(
            item=item2,
            term=term
        )
        
        # Verify the same term is used in both contexts
        self.assertEqual(item_term1.term.id, term.id, "First item should use the same term")
        self.assertEqual(item_term2.term.id, term.id, "Second item should use the same term")
        self.assertEqual(item_term1.term.id, item_term2.term.id, "Both items should use the exact same term")
        
        # Verify the term is linked to the same taxonomy in both cases
        self.assertEqual(item_term1.term.taxonomy.id, taxonomy.id)
        self.assertEqual(item_term2.term.taxonomy.id, taxonomy.id)
        
        # Verify only one term exists (no duplication)
        term_count = Term.objects.filter(taxonomy=taxonomy, value=term_value).count()
        self.assertEqual(term_count, 1, "Only one term should exist, reused across decisions")
        
        # Verify only one taxonomy exists (no duplication)
        taxonomy_count = Taxonomy.objects.filter(name=taxonomy_name).count()
        self.assertEqual(taxonomy_count, 1, "Only one taxonomy should exist, reused across decisions")
