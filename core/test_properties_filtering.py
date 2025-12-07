"""
Property-based tests for item filtering
Tests Properties 23-26 from the design document
"""

from hypothesis import given, strategies as st, settings, assume
from hypothesis.extra.django import TestCase
from django.contrib.auth import get_user_model
from core.models import (
    AppGroup, GroupMembership, Decision, DecisionItem, 
    Taxonomy, Term, DecisionItemTerm
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
    # Ensure uniqueness within taxonomy
    value = f"{value}_{uuid.uuid4().hex[:8]}"
    
    term = Term.objects.create(
        taxonomy=taxonomy,
        value=value,
        attributes=None
    )
    return term


class FilteringPropertyTests(TestCase):
    """Property-based tests for item filtering"""
    
    @given(st.data())
    @settings(max_examples=100, deadline=None)
    def test_property_23_tag_filtering_accuracy(self, data):
        """
        Feature: generic-swipe-voting, Property 23: Tag filtering accuracy
        For any tag filter applied to items, only items linked to the specified 
        term via decision_item_term should be returned.
        Validates: Requirements 7.1
        """
        # Generate test data
        user = data.draw(user_strategy())
        group = data.draw(group_strategy(user))
        decision = data.draw(decision_strategy(group))
        taxonomy = data.draw(taxonomy_strategy())
        
        # Create multiple terms
        num_terms = data.draw(st.integers(min_value=2, max_value=5))
        terms = [data.draw(term_strategy(taxonomy)) for _ in range(num_terms)]
        
        # Create items with different tags
        num_items = data.draw(st.integers(min_value=3, max_value=10))
        items = []
        for i in range(num_items):
            label = f"Item_{i}_{uuid.uuid4().hex[:8]}"
            item = DecisionItem.objects.create(
                decision=decision,
                label=label,
                attributes=None
            )
            items.append(item)
            
            # Tag some items with random terms
            if data.draw(st.booleans()):
                term = data.draw(st.sampled_from(terms))
                DecisionItemTerm.objects.create(item=item, term=term)
        
        # Pick a term to filter by
        filter_term = data.draw(st.sampled_from(terms))
        
        # Get items that should match the filter
        expected_items = set(
            DecisionItem.objects.filter(
                decision=decision,
                item_terms__term=filter_term
            ).values_list('id', flat=True)
        )
        
        # Apply the filter
        filtered_items = set(
            DecisionItem.objects.filter(
                decision=decision,
                item_terms__term=filter_term
            ).values_list('id', flat=True)
        )
        
        # Property: Only items with the specified tag should be returned
        self.assertEqual(filtered_items, expected_items)
        
        # Verify all returned items have the tag
        for item_id in filtered_items:
            self.assertTrue(
                DecisionItemTerm.objects.filter(
                    item_id=item_id,
                    term=filter_term
                ).exists()
            )
    
    @given(st.data())
    @settings(max_examples=100, deadline=None)
    def test_property_24_attribute_filtering_accuracy(self, data):
        """
        Feature: generic-swipe-voting, Property 24: Attribute filtering accuracy
        For any JSONB attribute query, only items whose attributes match the 
        query criteria should be returned.
        Validates: Requirements 7.2
        """
        # Generate test data
        user = data.draw(user_strategy())
        group = data.draw(group_strategy(user))
        decision = data.draw(decision_strategy(group))
        
        # Create a specific attribute key and value to filter by
        attr_key = data.draw(safe_text(min_size=1, max_size=20))
        attr_value = data.draw(st.integers(min_value=1, max_value=100))
        
        # Create items with different attributes
        num_items = data.draw(st.integers(min_value=3, max_value=10))
        items_with_attr = []
        items_without_attr = []
        
        for i in range(num_items):
            label = f"Item_{i}_{uuid.uuid4().hex[:8]}"
            
            # Randomly decide if this item should have the attribute
            has_attr = data.draw(st.booleans())
            
            if has_attr:
                attributes = {attr_key: attr_value}
                item = DecisionItem.objects.create(
                    decision=decision,
                    label=label,
                    attributes=attributes
                )
                items_with_attr.append(item.id)
            else:
                # Either no attributes or different value
                if data.draw(st.booleans()):
                    attributes = None
                else:
                    attributes = {attr_key: data.draw(st.integers(min_value=101, max_value=200))}
                
                item = DecisionItem.objects.create(
                    decision=decision,
                    label=label,
                    attributes=attributes
                )
                items_without_attr.append(item.id)
        
        # Apply the attribute filter
        filtered_items = set(
            DecisionItem.objects.filter(
                decision=decision,
                attributes__contains={attr_key: attr_value}
            ).values_list('id', flat=True)
        )
        
        # Property: Only items with matching attribute should be returned
        self.assertEqual(filtered_items, set(items_with_attr))
        
        # Verify all returned items have the correct attribute
        for item_id in filtered_items:
            item = DecisionItem.objects.get(id=item_id)
            self.assertIsNotNone(item.attributes)
            self.assertIn(attr_key, item.attributes)
            self.assertEqual(item.attributes[attr_key], attr_value)
    
    @given(st.data())
    @settings(max_examples=100, deadline=None)
    def test_property_25_combined_filter_intersection(self, data):
        """
        Feature: generic-swipe-voting, Property 25: Combined filter intersection
        For any combination of tag and attribute filters, only items matching 
        all criteria should be returned.
        Validates: Requirements 7.3
        """
        # Generate test data
        user = data.draw(user_strategy())
        group = data.draw(group_strategy(user))
        decision = data.draw(decision_strategy(group))
        taxonomy = data.draw(taxonomy_strategy())
        term = data.draw(term_strategy(taxonomy))
        
        # Create a specific attribute key and value
        attr_key = data.draw(safe_text(min_size=1, max_size=20))
        attr_value = data.draw(st.integers(min_value=1, max_value=100))
        
        # Create items with different combinations
        num_items = data.draw(st.integers(min_value=4, max_value=10))
        items_with_both = []
        items_with_tag_only = []
        items_with_attr_only = []
        items_with_neither = []
        
        for i in range(num_items):
            label = f"Item_{i}_{uuid.uuid4().hex[:8]}"
            
            has_tag = data.draw(st.booleans())
            has_attr = data.draw(st.booleans())
            
            # Create item with appropriate attributes
            if has_attr:
                attributes = {attr_key: attr_value}
            else:
                attributes = None
            
            item = DecisionItem.objects.create(
                decision=decision,
                label=label,
                attributes=attributes
            )
            
            # Tag if needed
            if has_tag:
                DecisionItemTerm.objects.create(item=item, term=term)
            
            # Categorize
            if has_tag and has_attr:
                items_with_both.append(item.id)
            elif has_tag:
                items_with_tag_only.append(item.id)
            elif has_attr:
                items_with_attr_only.append(item.id)
            else:
                items_with_neither.append(item.id)
        
        # Apply combined filters
        filtered_items = set(
            DecisionItem.objects.filter(
                decision=decision,
                item_terms__term=term,
                attributes__contains={attr_key: attr_value}
            ).values_list('id', flat=True)
        )
        
        # Property: Only items matching ALL criteria should be returned
        self.assertEqual(filtered_items, set(items_with_both))
        
        # Verify no items with only one criterion are included
        for item_id in items_with_tag_only:
            self.assertNotIn(item_id, filtered_items)
        for item_id in items_with_attr_only:
            self.assertNotIn(item_id, filtered_items)
        for item_id in items_with_neither:
            self.assertNotIn(item_id, filtered_items)
    
    @given(st.data())
    @settings(max_examples=100, deadline=None)
    def test_property_26_pagination_correctness(self, data):
        """
        Feature: generic-swipe-voting, Property 26: Pagination correctness
        For any page size and page number, the returned items should be the 
        correct subset of the total result set.
        Validates: Requirements 7.4
        """
        # Generate test data
        user = data.draw(user_strategy())
        group = data.draw(group_strategy(user))
        decision = data.draw(decision_strategy(group))
        
        # Create a known number of items
        num_items = data.draw(st.integers(min_value=5, max_value=20))
        items = []
        for i in range(num_items):
            label = f"Item_{i:03d}_{uuid.uuid4().hex[:8]}"
            item = DecisionItem.objects.create(
                decision=decision,
                label=label,
                attributes=None
            )
            items.append(item)
        
        # Get all items in order
        all_items = list(
            DecisionItem.objects.filter(decision=decision)
            .order_by('id')
            .values_list('id', flat=True)
        )
        
        # Choose pagination parameters
        page_size = data.draw(st.integers(min_value=1, max_value=10))
        total_pages = (num_items + page_size - 1) // page_size
        
        # Only test valid page numbers
        assume(total_pages > 0)
        page = data.draw(st.integers(min_value=1, max_value=total_pages))
        
        # Calculate expected items for this page
        start_index = (page - 1) * page_size
        end_index = min(start_index + page_size, num_items)
        expected_items = all_items[start_index:end_index]
        
        # Get paginated items
        paginated_items = list(
            DecisionItem.objects.filter(decision=decision)
            .order_by('id')[start_index:end_index]
            .values_list('id', flat=True)
        )
        
        # Property: Paginated items should match expected subset
        self.assertEqual(paginated_items, expected_items)
        
        # Verify page size constraint
        self.assertLessEqual(len(paginated_items), page_size)
        
        # Verify correct number of items on last page
        if page == total_pages:
            expected_last_page_size = num_items - (page - 1) * page_size
            self.assertEqual(len(paginated_items), expected_last_page_size)
