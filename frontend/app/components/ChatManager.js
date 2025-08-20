'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import ChatContainer from './ChatContainer';
import ChatSidebar from './ChatSidebar';
import { useKeycloak } from '../contexts/KeycloakContext';

// Custom hook for localStorage with cleanup support
const useLocalStorage = (key, defaultValue) => {
    const [value, setValue] = useState(defaultValue);
    
    useEffect(() => {
        if (typeof window === 'undefined') return;
        
        try {
            const saved = localStorage.getItem(key);
            if (saved) setValue(JSON.parse(saved));
        } catch (error) {
            console.error(`Error loading ${key}:`, error);
        }
    }, [key]);
    
    useEffect(() => {
        if (typeof window === 'undefined') return;
        
        if (value === defaultValue || value === null) {
            localStorage.removeItem(key);
        } else {
            localStorage.setItem(key, JSON.stringify(value));
        }
    }, [key, value, defaultValue]);
    
    const clearValue = useCallback(() => {
        setValue(defaultValue);
        if (typeof window !== 'undefined') {
            localStorage.removeItem(key);
        }
    }, [defaultValue, key]);
    
    return [value, setValue, clearValue];
};

// Helper to create a new local chat (fallback)
const createLocalChat = () => ({
    id: `chat-${Date.now()}-${Math.random().toString(36).substring(2)}`,
    title: '',
    messages: [],
    lastUpdated: new Date().toISOString(),
});

// Constants
const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;
const API_ENDPOINTS = {
    CHAT_SESSIONS: `${BACKEND_URL}/chat/sessions`,
    ASK_STREAM: '/api/ask/stream',
    SAVE_PARTIAL: `${BACKEND_URL}/chat/save_partial`,
};

const MESSAGES = {
    LOADING: 'Loading chat history...',
    NO_CHAT: 'No chat selected',
    CHECKING: '⏳ Checking if message is appropriate...',
    CANCELLED: '\n🛑 Response cancelled\n',
    ERROR: (msg) => `\n⚠️ Error: ${msg}\n`,
};


/**
 * ChatManager - Main component for managing D&D chat sessions
 * 
 * Features:
 * - User authentication integration with Keycloak
 * - Persistent chat history stored in MongoDB backend
 * - Real-time streaming responses
 * - Chat session CRUD operations (create, read, update, delete)
 * - Responsive sidebar with chat list
 * - Loading states and error handling
 * 
 * @returns {JSX.Element} The ChatManager component
 */
const ChatManager = () => {
    const [chats, setChats] = useState([]);
    const [activeChat, setActiveChat, clearActiveChat] = useLocalStorage('dnd-active-chat', null);
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const [loading, setLoading] = useState(true);
    const [loadingStates, setLoadingStates] = useState(new Map());
    
    // Refs for tracking active streams
    const activeStreamsRef = useRef(new Map());
    

    // Keycloak authentication context
    const { getToken, refreshToken, authenticated } = useKeycloak();


    // Helper function to create authorization headers
    const createAuthHeaders = useCallback((token) => {
        const headers = { 'Content-Type': 'application/json' };
        if (token) headers['Authorization'] = `Bearer ${token}`;
        return headers;
    }, []);


    // Helper function to format backend session to frontend format
    const formatSessionForFrontend = useCallback((session) => ({
        id: session.id,
        title: session.title || 'New chat',
        messages: session.messages.map(msg => ({
            content: msg.content,
            isUser: msg.is_user,
            timestamp: msg.timestamp
        })),
        lastUpdated: session.updated_at,
    }), []);


    // Load chat sessions from backend
    const loadChatSessions = useCallback(async () => {
        try {
            setLoading(true);
            const token = getToken();
            
            if (!token) {
                console.log('No token available, skipping chat load');
                setChats([]);
                clearActiveChat();
                return;
            }

            const response = await fetch(API_ENDPOINTS.CHAT_SESSIONS, {
                headers: createAuthHeaders(token),
            });

            if (response.ok) {
                const sessions = await response.json();
                console.log('Loaded chat sessions:', sessions.length);
                
                const formattedChats = sessions.map(formatSessionForFrontend);
                setChats(formattedChats);
                
                // Handle active chat selection
                if (!activeChat && formattedChats.length > 0) {
                    setActiveChat(formattedChats[0].id);
                } else if (activeChat && formattedChats.length > 0) {
                    const activeChatExists = formattedChats.some(chat => chat.id === activeChat);
                    if (!activeChatExists) {
                        setActiveChat(formattedChats[0].id);
                    }
                }
            } else if (response.status === 401) {
                console.log('Authentication failed, clearing chats');
                setChats([]);
                clearActiveChat();
            } else {
                console.error('Failed to load chat sessions:', response.status);
            }
        } catch (error) {
            console.error('Failed to load chat sessions:', error);
            setChats([]);
            clearActiveChat();
        } finally {
            setLoading(false);
        }
    }, [getToken, activeChat, setActiveChat, clearActiveChat, createAuthHeaders, formatSessionForFrontend]);


    // Authentication effect
    useEffect(() => {
        if (authenticated) {
            loadChatSessions();
        } else {
            setChats([]);
            clearActiveChat();
            setLoading(false);
        }
    }, [authenticated, clearActiveChat, loadChatSessions]);


    // Create a new chat session in backend
    const createChatSession = useCallback(async (title = 'New chat') => {
        try {
            const token = getToken();
            if (!token) return null;

            const response = await fetch(API_ENDPOINTS.CHAT_SESSIONS, {
                method: 'POST',
                headers: createAuthHeaders(token),
                body: JSON.stringify({ title }),
            });

            if (response.ok) {
                const session = await response.json();
                return formatSessionForFrontend(session);
            }
        } catch (error) {
            console.error('Failed to create chat session:', error);
        }
        return null;
    }, [getToken, createAuthHeaders, formatSessionForFrontend]);


    // Delete a chat session from backend
    const deleteChatSession = useCallback(async (chatId) => {
        try {
            const token = getToken();
            if (!token) return false;

            const response = await fetch(`${API_ENDPOINTS.CHAT_SESSIONS}/${chatId}`, {
                method: 'DELETE',
                headers: createAuthHeaders(token),
            });

            return response.ok;
        } catch (error) {
            console.error('Failed to delete chat session:', error);
            return false;
        }
    }, [getToken, createAuthHeaders]);


    // Update chat session title in backend
    const updateChatSessionTitle = useCallback(async (chatId, title) => {
        try {
            const token = getToken();
            if (!token) return false;

            const response = await fetch(`${API_ENDPOINTS.CHAT_SESSIONS}/${chatId}`, {
                method: 'PUT',
                headers: createAuthHeaders(token),
                body: JSON.stringify({ title }),
            });

            return response.ok;
        } catch (error) {
            console.error('Failed to update chat session title:', error);
            return false;
        }
    }, [getToken, createAuthHeaders]);


    // Event handlers
    const handleNewChat = useCallback(async () => {
        const token = getToken();
        
        if (token) {
            const newSession = await createChatSession();
            if (newSession) {
                setChats(prev => [newSession, ...prev]);
                setActiveChat(newSession.id);
                return;
            }
        }
        
        const newChat = createLocalChat();
        setChats(prev => [newChat, ...prev]);
        setActiveChat(newChat.id);
    }, [getToken, createChatSession, setActiveChat]);

    const handleChatSelect = useCallback((chatId) => {
        setActiveChat(chatId);
    }, [setActiveChat]);

    const handleDeleteChat = useCallback(async (chatId) => {
        const abortController = activeStreamsRef.current.get(chatId);
        if (abortController) {
            abortController.abort();
            activeStreamsRef.current.delete(chatId);
        }
        
        // Delete from backend if authenticated
        const token = getToken();
        if (token) {
            const success = await deleteChatSession(chatId);
            if (!success) {
                console.warn('Failed to delete chat session from backend');
            }
        }
        
        setChats(prev => {
            const filteredChats = prev.filter(chat => chat.id !== chatId);
            
            // Handle active chat selection after deletion
            if (chatId === activeChat) {
                if (filteredChats.length > 0) {
                    setActiveChat(filteredChats[0].id);
                } else {
                    clearActiveChat();
                }
            }
            return filteredChats;
        });
    }, [activeChat, setActiveChat, clearActiveChat, getToken, deleteChatSession]);


    // Handle chat title editing
    const handleEditTitle = useCallback(async (chatId, newTitle) => {
        setChats(prev => prev.map(chat =>
            chat.id === chatId ? { ...chat, title: newTitle } : chat
        ));
        
        // Save to database
        const token = getToken();
        if (token) {
            const success = await updateChatSessionTitle(chatId, newTitle);
            if (!success) {
                console.warn('Failed to update chat title in database');
            }
        }
    }, [getToken, updateChatSessionTitle]);


    // Helper function to update chat messages
    const updateChatMessage = useCallback((chatId, messageId, newContent) => {
        setChats(prev => prev.map(chat =>
            chat.id === chatId ? {
                ...chat,
                messages: chat.messages.map(msg =>
                    msg.id === messageId ? { ...msg, content: newContent } : msg
                ),
                lastUpdated: new Date().toISOString()
            } : chat
        ));
    }, []);

    const addMessagesToChat = useCallback(async (chatId, newMessages, updateTitle = false) => {
        let newTitleGenerated = null;
        
        setChats(prev => prev.map(chat =>
            chat.id === chatId ? {
                ...chat,
                messages: [...chat.messages, ...newMessages],
                lastUpdated: new Date().toISOString(),
                title: (() => {
                    if (updateTitle && (!chat.title || chat.title === '' || chat.title === 'New chat')) {
                        const generatedTitle = newMessages.find(msg => msg.isUser)?.content.slice(0, 30) || 'New chat';
                        newTitleGenerated = generatedTitle;
                        return generatedTitle;
                    }
                    return chat.title;
                })()
            } : chat
        ));
        
        // Save the new title to the database if one was generated
        if (newTitleGenerated && getToken()) {
            await updateChatSessionTitle(chatId, newTitleGenerated);
        }
    }, [getToken, updateChatSessionTitle]);

    const fetchWithAuthRetry = useCallback(async (url, options) => {
        const token = getToken();
        let response = await fetch(url, {
            ...options,
            headers: { ...options.headers, ...createAuthHeaders(token) }
        });

        // Handle authentication retry
        if (response.status === 401) {
            const refreshed = await refreshToken();
            if (refreshed) {
                const newToken = getToken();
                response = await fetch(url, {
                    ...options,
                    headers: { ...options.headers, ...createAuthHeaders(newToken) }
                });
            }
            
            if (!response.ok) {
                throw new Error('Authentication failed. Please sign in again.');
            }
        } else if (!response.ok) {
            throw new Error(`Error ${response.status}: ${response.statusText}`);
        }

        return response;
    }, [getToken, refreshToken, createAuthHeaders]);

    const setLoadingForChat = useCallback((chatId, isLoading) => {
        setLoadingStates(prev => {
            const newStates = new Map(prev);
            if (isLoading) {
                newStates.set(chatId, true);
            } else {
                newStates.delete(chatId);
            }
            return newStates;
        });
    }, []);


    const handleStreamStart = useCallback((chatId, abortController) => {
        activeStreamsRef.current.set(chatId, abortController);
        setLoadingForChat(chatId, true);
    }, [setLoadingForChat]);


    const handleStreamEnd = useCallback((chatId) => {
        activeStreamsRef.current.delete(chatId);
        setLoadingForChat(chatId, false);
    }, [setLoadingForChat]);


    const handleAbortStream = useCallback(async (chatId) => {
        const abortController = activeStreamsRef.current.get(chatId);
        if (abortController) {
            // Find the current partial response before aborting
            const chat = chats.find(c => c.id === chatId);
            if (chat && chat.messages.length > 0) {
                const lastMessage = chat.messages[chat.messages.length - 1];
                // Only save if it's a non-user message and has content
                if (!lastMessage.isUser && lastMessage.content && lastMessage.content !== MESSAGES.CHECKING) {
                    try {
                        const token = getToken();
                        if (token) {
                            await fetch(API_ENDPOINTS.SAVE_PARTIAL, {
                                method: 'POST',
                                headers: createAuthHeaders(token),
                                body: JSON.stringify({
                                    session_id: chatId,
                                    partial_response: lastMessage.content
                            }),
                        });
                        }
                    } catch (error) {
                        console.error('Failed to save partial response:', error);
                    }
                }
            }
            
            abortController.abort();
            activeStreamsRef.current.delete(chatId);
            setLoadingForChat(chatId, false);
        }
    }, [chats, getToken, createAuthHeaders, setLoadingForChat]);


    const streamResponse = useCallback(async (chatId, question) => {
        handleAbortStream(chatId);
        
        const abortController = new AbortController();
        const responseId = Date.now().toString();
        
        const userMessage = { content: question, isUser: true };
        const placeholderMessage = { 
            id: responseId, 
            content: MESSAGES.CHECKING, 
            isUser: false 
        };
        
        await addMessagesToChat(chatId, [userMessage, placeholderMessage], true);
        handleStreamStart(chatId, abortController);

        try {
            const response = await fetchWithAuthRetry(API_ENDPOINTS.ASK_STREAM, {
                method: 'POST',
                body: JSON.stringify({ 
                    question,
                    session_id: chatId 
                }),
                signal: abortController.signal
            });

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let text = '';

            while (true) {
                if (abortController.signal.aborted) {
                    reader.cancel();
                    break;
                }

                const { done, value } = await reader.read();
                if (done) break;

                text += decoder.decode(value, { stream: true });
                updateChatMessage(chatId, responseId, text);
            }
        } catch (error) {
            const errorMessage = error.name === 'AbortError'
                ? MESSAGES.CANCELLED
                : MESSAGES.ERROR(error.message);

            setChats(prev => prev.map(chat =>
                chat.id === chatId ? {
                    ...chat,
                    messages: chat.messages.map(msg =>
                        msg.id === responseId 
                            ? { ...msg, content: msg.content + errorMessage }
                            : msg
                    ),
                    lastUpdated: new Date().toISOString()
                } : chat
            ));
        } finally {
            handleStreamEnd(chatId);
        }
    }, [handleAbortStream, handleStreamStart, handleStreamEnd, fetchWithAuthRetry, addMessagesToChat, updateChatMessage]);

    const currentChat = chats.find(chat => chat.id === activeChat);
    const isCurrentChatLoading = loadingStates.get(activeChat) || false;
    const isAnyStreamActive = loadingStates.size > 0;

    return (
        <div className="chat-manager">
            <button
                className="sidebar-toggle"
                onClick={() => setSidebarOpen(!sidebarOpen)}
                title={sidebarOpen ? 'Hide Sidebar' : 'Show Sidebar'}
                aria-label={sidebarOpen ? 'Hide Sidebar' : 'Show Sidebar'}
            >
                ☰
            </button>

            <div className={`chat-layout ${sidebarOpen ? 'sidebar-open' : 'sidebar-closed'}`}>
                {sidebarOpen && (
                    <ChatSidebar
                        chats={chats}
                        activeChat={activeChat}
                        onChatSelect={handleChatSelect}
                        onNewChat={handleNewChat}
                        onDeleteChat={handleDeleteChat}
                        onEditTitle={handleEditTitle}
                        isStreamActive={isAnyStreamActive}
                    />
                )}

                <div className="chat-main">
                    {loading ? (
                        <div className="loading-container">
                            <p>{MESSAGES.LOADING}</p>
                        </div>
                    ) : currentChat ? (
                        <ChatContainer
                            key={currentChat.id}
                            messages={currentChat.messages}
                            isLoading={isCurrentChatLoading}
                            onSubmit={(question) => streamResponse(currentChat.id, question)}
                            onCancel={() => handleAbortStream(currentChat.id)}
                        />
                    ) : (
                        <div className="no-chat-selected">
                            <p>{MESSAGES.NO_CHAT}</p>
                            <button 
                                onClick={handleNewChat}
                                disabled={isAnyStreamActive}
                            >
                                Start New Chat
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ChatManager;
