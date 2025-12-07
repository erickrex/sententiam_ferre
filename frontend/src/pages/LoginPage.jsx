import React from 'react';
import { Link, Navigate } from 'react-router-dom';
import LoginForm from '../components/LoginForm';
import { useAuth } from '../contexts/AuthContext';
import './LoginPage.css';

function LoginPage() {
  const { isAuthenticated } = useAuth();

  // Redirect to groups if already authenticated
  if (isAuthenticated) {
    return <Navigate to="/groups" replace />;
  }

  return (
    <div className="login-page">
      <div className="auth-container">
        <div className="auth-header">
          <h1>Welcome Back</h1>
          <p>Log in to continue making decisions together</p>
        </div>
        
        <LoginForm />
        
        <div className="auth-footer">
          <p>
            Don't have an account?{' '}
            <Link to="/signup" className="auth-link">
              Sign up
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
