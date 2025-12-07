import React, { useState, useEffect } from 'react';
import { groupsAPI } from '../services/api';
import JoinRequestForm from './JoinRequestForm';
import InviteUserForm from './InviteUserForm';
import MyJoinRequestsList from './MyJoinRequestsList';
import MyInvitationsList from './MyInvitationsList';
import Toast from './Toast';
import SkeletonLoader from './SkeletonLoader';
import './JoinTab.css';

function JoinTab() {
  const [myRequests, setMyRequests] = useState([]);
  const [myInvitations, setMyInvitations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [requestsResponse, invitationsResponse] = await Promise.all([
        groupsAPI.listMyRequests(),
        groupsAPI.listMyInvitations(),
      ]);
      
      // Handle different response formats
      const requestsData = requestsResponse.data.data || requestsResponse.data.results || requestsResponse.data;
      const invitationsData = invitationsResponse.data.data || invitationsResponse.data.results || invitationsResponse.data;
      
      setMyRequests(Array.isArray(requestsData) ? requestsData : []);
      setMyInvitations(Array.isArray(invitationsData) ? invitationsData : []);
    } catch (err) {
      showToast(err.message || 'Failed to load data', 'error');
    } finally {
      setLoading(false);
    }
  };

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
  };

  const handleJoinRequest = async (groupName) => {
    await groupsAPI.createJoinRequest(groupName);
    await loadData();
  };

  const handleResendRequest = async (requestId) => {
    await groupsAPI.manageMyRequest(requestId, 'resend');
    await loadData();
  };

  const handleDeleteRequest = async (requestId) => {
    await groupsAPI.manageMyRequest(requestId, 'delete');
    await loadData();
  };

  const handleAcceptInvitation = async (invitationId) => {
    await groupsAPI.manageMyInvitation(invitationId, 'accept');
    await loadData();
  };

  const handleRejectInvitation = async (invitationId) => {
    await groupsAPI.manageMyInvitation(invitationId, 'reject');
    await loadData();
  };

  return (
    <div className="join-tab">
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}

      <section className="invite-section">
        <h2 className="section-title">Send Invitation</h2>
        <p className="section-description">
          Invite users to join your groups
        </p>
        <InviteUserForm
          onSuccess={showToast}
          onError={(msg) => showToast(msg, 'error')}
        />
      </section>

      <section className="join-requests-section">
        <h2 className="section-title">Request to Join a Group</h2>
        <JoinRequestForm
          onSubmit={handleJoinRequest}
          onSuccess={showToast}
          onError={(msg) => showToast(msg, 'error')}
        />
        
        {loading ? (
          <>
            <h3 className="subsection-title">My Join Requests</h3>
            <SkeletonLoader type="card" count={2} />
          </>
        ) : myRequests.length > 0 ? (
          <>
            <h3 className="subsection-title">My Join Requests</h3>
            <MyJoinRequestsList
              requests={myRequests}
              onResend={handleResendRequest}
              onDelete={handleDeleteRequest}
              onSuccess={showToast}
              onError={(msg) => showToast(msg, 'error')}
            />
          </>
        ) : null}
      </section>

      <section className="invitations-section">
        <h2 className="section-title">Received Invitations</h2>
        {loading ? (
          <SkeletonLoader type="card" count={2} />
        ) : (
          <MyInvitationsList
            invitations={myInvitations}
            onAccept={handleAcceptInvitation}
            onReject={handleRejectInvitation}
            onSuccess={showToast}
            onError={(msg) => showToast(msg, 'error')}
          />
        )}
      </section>
    </div>
  );
}

export default JoinTab;
