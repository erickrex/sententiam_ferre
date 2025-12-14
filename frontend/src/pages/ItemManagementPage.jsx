import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ItemList from '../components/ItemList';
import AddItemForm from '../components/AddItemForm';
import ItemFilter from '../components/ItemFilter';
import Toast from '../components/Toast';
import CharacterCreationForm from '../components/CharacterCreationForm';
import CharacterGallery from '../components/CharacterGallery';
import { itemsAPI, taxonomiesAPI, decisionsAPI, generationAPI } from '../services/api';
import './ItemManagementPage.css';

function ItemManagementPage() {
  const { decisionId } = useParams();
  const navigate = useNavigate();
  
  const [decision, setDecision] = useState(null);
  const [items, setItems] = useState([]);
  const [taxonomies, setTaxonomies] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [filters, setFilters] = useState({ tags: [], attributes: {} });
  const [toast, setToast] = useState(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [isGenerating, setIsGenerating] = useState(false);

  // Check if this is a 2D character decision
  const isCharacterDecision = decision?.item_type === '2d_character';
  const lockedParams = decision?.rules?.locked_params || {};

  useEffect(() => {
    loadData();
  }, [decisionId]);

  useEffect(() => {
    if (!isLoading) {
      loadItems();
    }
  }, [filters]);

  const loadData = async () => {
    try {
      setIsLoading(true);
      
      // Load decision details
      const decisionResponse = await decisionsAPI.get(decisionId);
      setDecision(decisionResponse.data.data);
      
      // Check if user is admin (simplified - in real app, check membership role)
      setIsAdmin(true);
      
      // Load taxonomies with terms
      const taxonomiesResponse = await taxonomiesAPI.list();
      const taxonomiesData = taxonomiesResponse.data.data || [];
      
      // Load terms for each taxonomy
      const taxonomiesWithTerms = await Promise.all(
        taxonomiesData.map(async (taxonomy) => {
          try {
            const termsResponse = await taxonomiesAPI.listTerms(taxonomy.id);
            return {
              ...taxonomy,
              terms: termsResponse.data.data || []
            };
          } catch (err) {
            console.error(`Failed to load terms for taxonomy ${taxonomy.id}:`, err);
            return {
              ...taxonomy,
              terms: []
            };
          }
        })
      );
      
      setTaxonomies(taxonomiesWithTerms);
      
      // Load items
      await loadItems();
    } catch (err) {
      console.error('Failed to load data:', err);
      showToast('Failed to load data. Please try again.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const loadItems = async () => {
    try {
      const params = {};
      
      // Add tag filters
      if (filters.tags && filters.tags.length > 0) {
        params.tags = filters.tags.join(',');
      }
      
      // Add attribute filters
      if (filters.attributes && Object.keys(filters.attributes).length > 0) {
        Object.entries(filters.attributes).forEach(([key, value]) => {
          params[key] = value;
        });
      }
      
      const response = await itemsAPI.list(decisionId, params);
      setItems(response.data.data?.results || response.data.data || []);
    } catch (err) {
      console.error('Failed to load items:', err);
      showToast('Failed to load items. Please try again.', 'error');
    }
  };

  const handleAddItem = async (itemData) => {
    try {
      await itemsAPI.create(decisionId, itemData);
      showToast('Item added successfully!', 'success');
      setShowAddForm(false);
      await loadItems();
    } catch (err) {
      console.error('Failed to add item:', err);
      throw err;
    }
  };

  // Handle character generation (for 2D character decisions)
  const handleCreateCharacter = async (characterData) => {
    try {
      setIsGenerating(true);
      await generationAPI.createGeneration(decisionId, characterData);
      showToast('Character generation started! It will appear in the gallery shortly.', 'success');
      setShowAddForm(false);
      setRefreshTrigger(prev => prev + 1);
    } catch (err) {
      console.error('Failed to create character:', err);
      showToast(err.message || 'Failed to create character', 'error');
      throw err;
    } finally {
      setIsGenerating(false);
    }
  };

  // Handle creating a variation of an existing character
  const handleCreateVariation = async (item) => {
    // Pre-fill the form with the parent's parameters
    setEditingItem({
      ...item,
      isVariation: true,
      parentItemId: item.id,
    });
    setShowAddForm(true);
  };

  // Handle viewing character details
  const handleViewDetails = (item) => {
    // Could navigate to a detail page or show a modal
    console.log('View details for:', item);
  };

  const handleEditItem = async (itemData) => {
    try {
      await itemsAPI.update(editingItem.id, itemData);
      showToast('Item updated successfully!', 'success');
      setEditingItem(null);
      await loadItems();
    } catch (err) {
      console.error('Failed to update item:', err);
      throw err;
    }
  };

  const handleDeleteItem = async (itemId) => {
    if (!window.confirm('Are you sure you want to delete this item?')) {
      return;
    }

    try {
      await itemsAPI.delete(itemId);
      showToast('Item deleted successfully!', 'success');
      await loadItems();
    } catch (err) {
      console.error('Failed to delete item:', err);
      showToast('Failed to delete item. Please try again.', 'error');
    }
  };

  const handleFilterChange = (newFilters) => {
    setFilters(newFilters);
  };

  const showToast = (message, type = 'info') => {
    setToast({ message, type });
  };

  const handleCloseToast = () => {
    setToast(null);
  };

  if (isLoading) {
    return (
      <div className="item-management-page">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading items...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="item-management-page">
      <div className="page-header">
        <div className="header-content">
          <button
            className="back-button"
            onClick={() => navigate(`/decisions/${decisionId}`)}
          >
            ← Back
          </button>
          <div className="header-info">
            <h1 className="page-title">Manage Items</h1>
            {decision && (
              <p className="decision-name">{decision.title}</p>
            )}
          </div>
        </div>
        
        {isAdmin && !showAddForm && !editingItem && (
          <button
            className="add-item-button"
            onClick={() => setShowAddForm(true)}
          >
            {isCharacterDecision ? '+ Create Character' : '+ Add Item'}
          </button>
        )}
      </div>

      {/* Character Creation Form (for 2D character decisions) */}
      {isCharacterDecision && (showAddForm || editingItem) && (
        <div className="form-container">
          <CharacterCreationForm
            lockedParams={lockedParams}
            onSubmit={handleCreateCharacter}
            onCancel={() => {
              setShowAddForm(false);
              setEditingItem(null);
            }}
            isSubmitting={isGenerating}
          />
        </div>
      )}

      {/* Regular Item Form (for non-character decisions) */}
      {!isCharacterDecision && (showAddForm || editingItem) && (
        <div className="form-container">
          <AddItemForm
            onSubmit={editingItem ? handleEditItem : handleAddItem}
            onCancel={() => {
              setShowAddForm(false);
              setEditingItem(null);
            }}
            initialData={editingItem}
            taxonomies={taxonomies}
          />
        </div>
      )}

      {/* Character Gallery (for 2D character decisions) */}
      {isCharacterDecision && !showAddForm && !editingItem && (
        <div className="items-container">
          <CharacterGallery
            decisionId={decisionId}
            onCreateVariation={handleCreateVariation}
            onViewDetails={handleViewDetails}
            refreshTrigger={refreshTrigger}
          />
        </div>
      )}

      {/* Regular Item List (for non-character decisions) */}
      {!isCharacterDecision && !showAddForm && !editingItem && (
        <>
          <ItemFilter
            taxonomies={taxonomies}
            onFilterChange={handleFilterChange}
          />

          <div className="items-container">
            <div className="items-header">
              <h2 className="items-count">
                {items.length} {items.length === 1 ? 'Item' : 'Items'}
              </h2>
            </div>

            <ItemList
              items={items}
              onEdit={(item) => setEditingItem(item)}
              onDelete={handleDeleteItem}
              isAdmin={isAdmin}
            />
          </div>
        </>
      )}

      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={handleCloseToast}
        />
      )}
    </div>
  );
}

export default ItemManagementPage;
