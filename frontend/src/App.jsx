import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navigation from './components/Navigation';
import ProtectedRoute from './components/ProtectedRoute';
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import GroupsPage from './pages/GroupsPage';
import GroupDetailPage from './pages/GroupDetailPage';
import CreateDecisionPage from './pages/CreateDecisionPage';
import DecisionDetailPage from './pages/DecisionDetailPage';
import VotingPage from './pages/VotingPage';
import FavouritesPage from './pages/FavouritesPage';
import ItemManagementPage from './pages/ItemManagementPage';
import './App.css';

function App() {
  return (
    <Router>
      <div className="app">
        <Navigation />
        <main className="main-content">
          <Routes>
            {/* Public routes */}
            <Route path="/" element={<HomePage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/signup" element={<SignupPage />} />
            
            {/* Protected routes */}
            <Route 
              path="/groups" 
              element={
                <ProtectedRoute>
                  <GroupsPage />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/groups/:groupId" 
              element={
                <ProtectedRoute>
                  <GroupDetailPage />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/groups/:groupId/decisions/new" 
              element={
                <ProtectedRoute>
                  <CreateDecisionPage />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/decisions/:decisionId" 
              element={
                <ProtectedRoute>
                  <DecisionDetailPage />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/decisions/:decisionId/vote" 
              element={
                <ProtectedRoute>
                  <VotingPage />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/decisions/:decisionId/favourites" 
              element={
                <ProtectedRoute>
                  <FavouritesPage />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/decisions/:decisionId/items" 
              element={
                <ProtectedRoute>
                  <ItemManagementPage />
                </ProtectedRoute>
              } 
            />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
