'use client';

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import Keycloak from 'keycloak-js';

const KeycloakContext = createContext(null);

export const useKeycloak = () => {
  const context = useContext(KeycloakContext);
  if (!context) {
    throw new Error('useKeycloak must be used within a KeycloakProvider');
  }
  return context;
};

export const KeycloakProvider = ({ children }) => {
  const [keycloak, setKeycloak] = useState(null);
  const [authenticated, setAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [userInfo, setUserInfo] = useState(null);

  const initKeycloak = useCallback(async () => {
    try {
      const keycloakConfig = {
        url: process.env.NEXT_PUBLIC_KEYCLOAK_URL,
        realm: process.env.NEXT_PUBLIC_KEYCLOAK_REALM,
        clientId: process.env.NEXT_PUBLIC_KEYCLOAK_CLIENT_ID,
      };

      const kc = new Keycloak(keycloakConfig);
      
      const authenticated = await kc.init({
        onLoad: 'check-sso',
        silentCheckSsoRedirectUri: window.location.origin + '/silent-check-sso.html',
        checkLoginIframe: false,
      });

      setKeycloak(kc);
      setAuthenticated(authenticated);
      
      if (authenticated) {
        try {
          const userProfile = await kc.loadUserProfile();
          setUserInfo({
            id: kc.subject,
            username: kc.tokenParsed?.preferred_username,
            email: userProfile.email,
            firstName: userProfile.firstName,
            lastName: userProfile.lastName,
            fullName: `${userProfile.firstName || ''} ${userProfile.lastName || ''}`.trim(),
            roles: kc.tokenParsed?.realm_access?.roles || [],
          });
        } catch (error) {
          console.error('Failed to load user profile:', error);
        }
      }
    } catch (error) {
      console.error('Keycloak initialization failed:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    initKeycloak();
  }, [initKeycloak]);

  const login = useCallback(() => {
    if (keycloak) {
      keycloak.login();
    }
  }, [keycloak]);

  const logout = useCallback(() => {
    if (keycloak) {
      keycloak.logout();
    }
  }, [keycloak]);

  const getToken = useCallback(() => {
    return keycloak?.token;
  }, [keycloak]);

  const refreshToken = useCallback(async () => {
    if (keycloak) {
      try {
        const refreshed = await keycloak.updateToken(30);
        return refreshed;
      } catch (error) {
        console.error('Token refresh failed:', error);
        return false;
      }
    }
    return false;
  }, [keycloak]);

  const hasRole = useCallback((role) => {
    return userInfo?.roles?.includes(role) || false;
  }, [userInfo]);

  const value = {
    keycloak,
    authenticated,
    loading,
    userInfo,
    login,
    logout,
    getToken,
    refreshToken,
    hasRole,
  };

  return (
    <KeycloakContext.Provider value={value}>
      {children}
    </KeycloakContext.Provider>
  );
};
