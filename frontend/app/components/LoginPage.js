'use client';

import React from 'react';
import { useKeycloak } from '../contexts/KeycloakContext';

const LoginPage = () => {
  const { login, loading } = useKeycloak();

  if (loading) {
    return (
      <div className="login-container">
        <div className="login-box">
          <h1>D&D Agent</h1>
          <p>Loading authentication...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="login-container">
      <div className="login-box">
        <h1>🐉 D&D Agent</h1>
        <p>Your intelligent Dungeons & Dragons assistant</p>
        <div className="login-content">
          <p>Please sign in to access the D&D knowledge base and start asking questions about Dungeons & Dragons 5th Edition.</p>
          <button onClick={login} className="login-button">
            Sign In
          </button>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
