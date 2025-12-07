import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import './Navigation.css';

function Navigation() {
  const navigate = useNavigate();
  const { isAuthenticated, logout, user } = useAuth();
  
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
              <Link to="/groups" className="nav-link">Groups</Link>
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
