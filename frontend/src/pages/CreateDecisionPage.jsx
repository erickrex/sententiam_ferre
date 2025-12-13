import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { decisionsAPI } from '../services/api';
import CreateDecisionForm from '../components/CreateDecisionForm';
import './CreateDecisionPage.css';

function CreateDecisionPage() {
  const { groupId } = useParams();
  const navigate = useNavigate();

  const handleSubmit = async (decisionData) => {
    try {
      const response = await decisionsAPI.create(decisionData);
      // Navigate to the newly created decision
      const decisionId = response.data.data?.id || response.data.id;
      navigate(`/decisions/${decisionId}`);
    } catch (err) {
      throw new Error(err.message || 'Failed to create decision');
    }
  };

  const handleCancel = () => {
    navigate(`/groups/${groupId}`);
  };

  return (
    <div className="create-decision-page">
      <div className="page-container">
        <CreateDecisionForm
          groupId={groupId}
          onSubmit={handleSubmit}
          onCancel={handleCancel}
        />
      </div>
    </div>
  );
}

export default CreateDecisionPage;
