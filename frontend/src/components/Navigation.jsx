import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { groupsAPI } from '../services/api';
import './Navigation.css';

function Navigation() {
  const navigate = useNavigate();
  const { isAuthenticated, logout, user } = useAuth();
  const [pendingCount, setPendingCount] = useState(0);
  
  // Fetch pending invitations count
  useEffect(() => {
    const fetchPendingCount = async () => {
      if (!isAuthenticated) {
        setPendingCount(0);
        return;
      }
      
      try {
        const response = await groupsAPI.listMyInvitations();
        const invitations = response.data.data || response.data.results || response.data;
        const pending = Array.isArray(invitations) 
          ? invitations.filter(inv => inv.status === 'pending').length 
          : 0;
        setPendingCount(pending);
      } catch (err) {
        console.error('Failed to fetch pending invitations:', err);
      }
    };
    
    fetchPendingCount();
    
    // Poll every 30 seconds for new invitations
    const interval = setInterval(fetchPendingCount, 30000);
    return () => clearInterval(interval);
  }, [isAuthenticated]);
  
  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };
  
  return (
    <nav className="navigation">
      <div className="nav-container">
        <Link to="/" className="nav-brand">
          Sententiam Ferre
        </Link>
        
        <div className="nav-links">
          {isAuthenticated ? (
            <>
              {user && <span className="nav-username">Hi, {user.username}</span>}
              <Link to="/groups" className="nav-link nav-link-with-badge">
                Groups
                {pendingCount > 0 && (
                  <span className="notification-badge" title={`${pendingCount} pending invitation${pendingCount > 1 ? 's' : ''}`}>
                    {pendingCount > 9 ? '9+' : pendingCount}
                  </span>
                )}
              </Link>
              <button onClick={handleLogout} className="nav-link nav-button">
                Logout
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="nav-link">Login</Link>
              <Link to="/signup" className="nav-link">Sign Up</Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}

export default Navigation;
