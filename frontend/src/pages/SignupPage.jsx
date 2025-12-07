import React from 'react';
import { Link, Navigate } from 'react-router-dom';
import SignupForm from '../components/SignupForm';
import { useAuth } from '../contexts/AuthContext';
import './SignupPage.css';

function SignupPage() {
  const { isAuthenticated } = useAuth();

  // Redirect to groups if already authenticated
  if (isAuthenticated) {
    return <Navigate to="/groups" replace />;
  }

  return (
    <div className="signup-page">
      <div className="auth-container">
        <div className="auth-header">
          <h1>Create Account</h1>
          <p>Join Sententiam Ferre to start making decisions together</p>
        </div>
        
        <SignupForm />
        
        <div className="auth-footer">
          <p>
            Already have an account?{' '}
            <Link to="/login" className="auth-link">
              Log in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

export default SignupPage;
