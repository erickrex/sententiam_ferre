import React from 'react';
import { groupsAPI } from '../services/api';
import MyGroupsTab from '../components/MyGroupsTab';
import JoinTab from '../components/JoinTab';
import CreateGroupForm from '../components/CreateGroupForm';
import { Tabs, Tab } from '../components/Tabs';
import './GroupsPage.css';

function GroupsPage() {
  const handleCreateGroup = async (groupData) => {
    try {
      await groupsAPI.create(groupData);
    } catch (err) {
      throw new Error(err.message || 'Failed to create group');
    }
  };

  return (
    <div className="groups-page">
      <div className="page-header">
        <h1 className="page-title">Groups</h1>
      </div>

      <Tabs defaultTab={0}>
        <Tab label="My Groups">
          <MyGroupsTab />
        </Tab>
        <Tab label="Join">
          <JoinTab />
        </Tab>
        <Tab label="Create">
          <div className="create-tab">
            <CreateGroupForm 
              onSubmit={handleCreateGroup}
            />
          </div>
        </Tab>
      </Tabs>
    </div>
  );
}

export default GroupsPage;
