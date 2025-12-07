import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { groupsAPI, decisionsAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import GroupDetail from '../components/GroupDetail';
import DecisionList from '../components/DecisionList';
import InviteModal from '../components/InviteModal';
import JoinRequestsList from '../components/JoinRequestsList';
import RejectedInvitationsList from '../components/RejectedInvitationsList';
import RejectedRequestsList from '../components/RejectedRequestsList';
import Toast from '../components/Toast';
import SkeletonLoader from '../components/SkeletonLoader';
import './GroupDetailPage.css';

function GroupDetailPage() {
  const { groupId } = useParams();
  const { user } = useAuth();
  
  const [group, setGroup] = useState(null);
  const [members, setMembers] = useState([]);
  const [decisions, setDecisions] = useState([]);
  const [filteredDecisions, setFilteredDecisions] = useState([]);
  const [statusFilter, setStatusFilter] = useState('all');
  const [pendingInvitations, setPendingInvitations] = useState([]);
  const [joinRequests, setJoinRequests] = useState([]);
  const [rejectedInvitations, setRejectedInvitations] = useState([]);
  const [rejectedRequests, setRejectedRequests] = useState([]);
  const [activeTab, setActiveTab] = useState('decisions');
  const [loading, setLoading] = useState(true);
  const [adminDataLoading, setAdminDataLoading] = useState(false);
  const [error, setError] = useState('');
  const [toast, setToast] = useState(null);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [collapsedSections, setCollapsedSections] = useState({
    joinRequests: false,
    rejectedInvitations: false,
    rejectedRequests: false,
  });

  useEffect(() => {
    loadGroupData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [groupId]);

  useEffect(() => {
    // Filter decisions based on status
    if (statusFilter === 'all') {
      setFilteredDecisions(decisions);
    } else {
      setFilteredDecisions(decisions.filter(d => d.status === statusFilter));
    }
  }, [decisions, statusFilter]);

  const loadGroupData = async () => {
    try {
      setLoading(true);
      setError('');
      
      const promises = [
        groupsAPI.get(groupId),
        groupsAPI.listMembers(groupId),
        decisionsAPI.listByGroup(groupId),
      ];
      
      // Check if user is admin to load admin-specific data
      const [groupResponse, membersResponse, decisionsResponse] = await Promise.all(promises);
      
      // Extract nested data from responses
      const groupData = groupResponse.data.data || groupResponse.data;
      const membersData = membersResponse.data.data || membersResponse.data.results || membersResponse.data;
      const decisionsData = decisionsResponse.data.data || decisionsResponse.data.results || decisionsResponse.data;
      
      setGroup(groupData);
      setMembers(Array.isArray(membersData) ? membersData : []);
      setDecisions(Array.isArray(decisionsData) ? decisionsData : []);
      
      // Check for pending invitations for current user
      const membersList = Array.isArray(membersData) ? membersData : [];
      const userMembership = membersList.find(m => m.user_id === user?.id);
      if (userMembership && !userMembership.is_confirmed) {
        setPendingInvitations([userMembership]);
      }
      
      // Load admin-specific data if user is admin
      const isUserAdmin = membersList.find(m => m.user_id === user?.id)?.role === 'admin';
      if (isUserAdmin) {
        await loadAdminData();
      }
    } catch (err) {
      setError(err.message || 'Failed to load group data');
    } finally {
      setLoading(false);
    }
  };
  
  const loadAdminData = async () => {
    try {
      setAdminDataLoading(true);
      const [joinRequestsResponse, rejectedInvitationsResponse, rejectedRequestsResponse] = await Promise.all([
        groupsAPI.listGroupJoinRequests(groupId),
        groupsAPI.listRejectedInvitations(groupId),
        groupsAPI.listRejectedRequests(groupId),
      ]);
      
      const joinRequestsData = joinRequestsResponse.data.data || joinRequestsResponse.data.results || joinRequestsResponse.data;
      const rejectedInvitationsData = rejectedInvitationsResponse.data.data || rejectedInvitationsResponse.data.results || rejectedInvitationsResponse.data;
      const rejectedRequestsData = rejectedRequestsResponse.data.data || rejectedRequestsResponse.data.results || rejectedRequestsResponse.data;
      
      setJoinRequests(Array.isArray(joinRequestsData) ? joinRequestsData : []);
      setRejectedInvitations(Array.isArray(rejectedInvitationsData) ? rejectedInvitationsData : []);
      setRejectedRequests(Array.isArray(rejectedRequestsData) ? rejectedRequestsData : []);
    } catch (err) {
      console.error('Failed to load admin data:', err);
    } finally {
      setAdminDataLoading(false);
    }
  };

  const handleInvite = async (username) => {
    try {
      await groupsAPI.inviteMember(groupId, { username });
      await loadGroupData();
      showSuccess('Invitation sent successfully');
    } catch (err) {
      throw new Error(err.message || 'Failed to send invitation');
    }
  };

  const handleRemoveMember = async (userId) => {
    if (!window.confirm('Are you sure you want to remove this member?')) {
      return;
    }
    
    try {
      await groupsAPI.removeMember(groupId, userId);
      await loadGroupData();
    } catch (err) {
      setError(err.message || 'Failed to remove member');
    }
  };

  const handleAcceptInvitation = async () => {
    try {
      await groupsAPI.updateMembership(groupId, user.id, { is_confirmed: true });
      await loadGroupData();
    } catch (err) {
      setError(err.message || 'Failed to accept invitation');
    }
  };

  const handleDeclineInvitation = async () => {
    if (!window.confirm('Are you sure you want to decline this invitation?')) {
      return;
    }
    
    try {
      await groupsAPI.removeMember(groupId, user.id);
      window.location.href = '/groups';
    } catch (err) {
      setError(err.message || 'Failed to decline invitation');
    }
  };
  
  const handleApproveRequest = async (requestId) => {
    try {
      await groupsAPI.manageJoinRequest(groupId, requestId, 'approve');
      await loadGroupData();
    } catch (err) {
      throw err;
    }
  };
  
  const handleRejectRequest = async (requestId) => {
    try {
      await groupsAPI.manageJoinRequest(groupId, requestId, 'reject');
      await loadAdminData();
    } catch (err) {
      throw err;
    }
  };
  
  const handleResendInvitation = async (invitationId) => {
    try {
      await groupsAPI.manageRejectedInvitation(groupId, invitationId, 'resend');
      await loadAdminData();
    } catch (err) {
      throw err;
    }
  };
  
  const handleDeleteInvitation = async (invitationId) => {
    try {
      await groupsAPI.manageRejectedInvitation(groupId, invitationId, 'delete');
      await loadAdminData();
    } catch (err) {
      throw err;
    }
  };
  
  const handleDeleteRequest = async (requestId) => {
    try {
      await groupsAPI.manageRejectedRequest(groupId, requestId, 'delete');
      await loadAdminData();
    } catch (err) {
      throw err;
    }
  };
  
  const showSuccess = (message) => {
    setToast({ message, type: 'success' });
  };
  
  const showError = (message) => {
    setToast({ message, type: 'error' });
  };
  
  const toggleSection = (section) => {
    setCollapsedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  if (loading) {
    return <div className="loading-page">Loading group...</div>;
  }

  if (error && !group) {
    return (
      <div className="error-page">
        <p>{error}</p>
        <Link to="/groups" className="back-link">← Back to Groups</Link>
      </div>
    );
  }

  const isAdmin = members.find(m => m.user_id === user?.id)?.role === 'admin';

  return (
    <div className="group-detail-page">
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}

      <Link to="/groups" className="back-link">← Back to Groups</Link>

      {pendingInvitations.length > 0 && (
        <div className="invitation-banner">
          <div className="invitation-content">
            <p className="invitation-message">
              You've been invited to join <strong>{group.name}</strong>
            </p>
            <div className="invitation-actions">
              <button 
                className="accept-button"
                onClick={handleAcceptInvitation}
              >
                Accept
              </button>
              <button 
                className="decline-button"
                onClick={handleDeclineInvitation}
              >
                Decline
              </button>
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className="error-message">{error}</div>
      )}

      <div className="tabs">
        <button
          className={`tab ${activeTab === 'decisions' ? 'active' : ''}`}
          onClick={() => setActiveTab('decisions')}
        >
          Decisions ({decisions.length})
        </button>
        <button
          className={`tab ${activeTab === 'members' ? 'active' : ''}`}
          onClick={() => setActiveTab('members')}
        >
          Members ({members.filter(m => m.is_confirmed).length})
        </button>
      </div>

      <div className="tab-content">
        {activeTab === 'decisions' ? (
          <div className="decisions-tab">
            <div className="decisions-header">
              <h2 className="section-title">Decisions</h2>
              {isAdmin && (
                <Link to={`/groups/${groupId}/decisions/new`} className="create-decision-button">
                  + New Decision
                </Link>
              )}
            </div>
            
            <div className="filter-controls">
              <label htmlFor="status-filter" className="filter-label">
                Filter by status:
              </label>
              <select
                id="status-filter"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="status-filter"
              >
                <option value="all">All Statuses</option>
                <option value="draft">Draft</option>
                <option value="open">Open</option>
                <option value="closed">Closed</option>
                <option value="archived">Archived</option>
              </select>
            </div>
            
            <DecisionList
              decisions={filteredDecisions}
              groupId={groupId}
              isAdmin={isAdmin}
            />
          </div>
        ) : (
          <div className="members-tab">
            <GroupDetail
              group={group}
              members={members}
              onInvite={() => setShowInviteModal(true)}
              onRemoveMember={handleRemoveMember}
              isAdmin={isAdmin}
            />
            
            {isAdmin && (
              <div className="admin-section">
                <div 
                  className="admin-section-header"
                  onClick={() => !adminDataLoading && toggleSection('joinRequests')}
                >
                  <h2 className="section-title">
                    Join Requests {!adminDataLoading && `(${joinRequests.length})`}
                  </h2>
                  {!adminDataLoading && (
                    <button 
                      className={`collapse-toggle ${collapsedSections.joinRequests ? 'collapsed' : ''}`}
                      aria-label={collapsedSections.joinRequests ? 'Expand section' : 'Collapse section'}
                    >
                      ▼
                    </button>
                  )}
                </div>
                <div className={`admin-section-content ${collapsedSections.joinRequests ? 'collapsed' : 'expanded'}`}>
                  {adminDataLoading ? (
                    <SkeletonLoader type="card" count={2} />
                  ) : (
                    <JoinRequestsList
                      requests={joinRequests}
                      onApprove={handleApproveRequest}
                      onReject={handleRejectRequest}
                      onSuccess={showSuccess}
                      onError={showError}
                    />
                  )}
                </div>
              </div>
            )}
            
            {isAdmin && rejectedInvitations.length > 0 && (
              <div className="admin-section">
                <div 
                  className="admin-section-header"
                  onClick={() => !adminDataLoading && toggleSection('rejectedInvitations')}
                >
                  <h2 className="section-title">Rejected Invitations</h2>
                  {!adminDataLoading && (
                    <button 
                      className={`collapse-toggle ${collapsedSections.rejectedInvitations ? 'collapsed' : ''}`}
                      aria-label={collapsedSections.rejectedInvitations ? 'Expand section' : 'Collapse section'}
                    >
                      ▼
                    </button>
                  )}
                </div>
                <div className={`admin-section-content ${collapsedSections.rejectedInvitations ? 'collapsed' : 'expanded'}`}>
                  {adminDataLoading ? (
                    <SkeletonLoader type="card" count={2} />
                  ) : (
                    <RejectedInvitationsList
                      invitations={rejectedInvitations}
                      onResend={handleResendInvitation}
                      onDelete={handleDeleteInvitation}
                      onSuccess={showSuccess}
                      onError={showError}
                    />
                  )}
                </div>
              </div>
            )}
            
            {isAdmin && rejectedRequests.length > 0 && (
              <div className="admin-section">
                <div 
                  className="admin-section-header"
                  onClick={() => !adminDataLoading && toggleSection('rejectedRequests')}
                >
                  <h2 className="section-title">Rejected Requests</h2>
                  {!adminDataLoading && (
                    <button 
                      className={`collapse-toggle ${collapsedSections.rejectedRequests ? 'collapsed' : ''}`}
                      aria-label={collapsedSections.rejectedRequests ? 'Expand section' : 'Collapse section'}
                    >
                      ▼
                    </button>
                  )}
                </div>
                <div className={`admin-section-content ${collapsedSections.rejectedRequests ? 'collapsed' : 'expanded'}`}>
                  {adminDataLoading ? (
                    <SkeletonLoader type="card" count={2} />
                  ) : (
                    <RejectedRequestsList
                      requests={rejectedRequests}
                      onDelete={handleDeleteRequest}
                      onSuccess={showSuccess}
                      onError={showError}
                    />
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      <InviteModal
        isOpen={showInviteModal}
        onClose={() => setShowInviteModal(false)}
        onInvite={handleInvite}
        groupName={group?.name}
      />
    </div>
  );
}

export default GroupDetailPage;
