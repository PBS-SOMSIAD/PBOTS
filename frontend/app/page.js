'use client';

import React from 'react';
import { useKeycloak } from './contexts/KeycloakContext';
import ChatManager from './components/ChatManager';
import LoginPage from './components/LoginPage';

export default function Home() {
  const { authenticated, loading } = useKeycloak();

  if (loading) {
    return (
      <div className="page">
        <div className="loading-container">
          <h1>D&D Agent</h1>
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  if (!authenticated) {
    return <LoginPage />;
  }

  return (
    <div className="page">
      <header>
        <div className="header-content">
          <div className="header-title">
            <h1>D&D Agent</h1>
            <p>Ask a question about Dungeons & Dragons 5th Edition</p>
          </div>
        </div>
      </header>
      
      <ChatManager />
    </div>
  );
}
