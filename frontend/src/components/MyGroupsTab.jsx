import React, { useState, useEffect } from 'react';
import { groupsAPI } from '../services/api';
import GroupList from './GroupList';
import SkeletonLoader from './SkeletonLoader';
import './MyGroupsTab.css';

function MyGroupsTab() {
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadGroups();
  }, []);

  const loadGroups = async () => {
    try {
      setLoading(true);
      setError('');
      const response = await groupsAPI.list();
      
      // Handle different response formats
      const groupsData = response.data.data || response.data.results || response.data;
      setGroups(Array.isArray(groupsData) ? groupsData : []);
    } catch (err) {
      setError(err.message || 'Failed to load groups');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="my-groups-tab">
        <SkeletonLoader type="card" count={3} />
      </div>
    );
  }

  return (
    <div className="my-groups-tab">
      <div className="tab-header">
        <h2 className="section-title">My Groups</h2>
        <p className="section-description">
          Groups you've created or joined
        </p>
      </div>
      
      <GroupList 
        groups={groups} 
        loading={loading} 
        error={error} 
      />
    </div>
  );
}

export default MyGroupsTab;
