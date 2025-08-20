'use client';

import React, { useState } from 'react';
import { useKeycloak } from '../contexts/KeycloakContext';

const ChatSidebar = ({ chats, activeChat, onChatSelect, onNewChat, onDeleteChat, onEditTitle, isStreamActive }) => {
  const { userInfo, logout } = useKeycloak();
  const [editingChatId, setEditingChatId] = useState(null);
  const [editingTitle, setEditingTitle] = useState('');

  const handleTitleEdit = (chatId, currentTitle) => {
    setEditingChatId(chatId);
    setEditingTitle(currentTitle);
  };

  const handleTitleSave = async () => {
    if (editingChatId && editingTitle.trim()) {
      await onEditTitle(editingChatId, editingTitle.trim());
    }
    setEditingChatId(null);
    setEditingTitle('');
  };

  const handleTitleCancel = () => {
    setEditingChatId(null);
    setEditingTitle('');
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleTitleSave();
    } else if (e.key === 'Escape') {
      handleTitleCancel();
    }
  };
  return (
    <div className="chat-sidebar">
      <div className="sidebar-header">
        <div className="header-top">
          {userInfo && (
            <div className="user-profile">
              <span className="user-name">
                Hello {userInfo.username}!
              </span>
              <button onClick={logout} className="logout-button">
                Sign Out
              </button>
            </div>
          )}
        </div>
        <div className="header-bottom">
          <span>Chat Sessions</span>
          <button 
            className="new-chat-btn"
            onClick={onNewChat}
            disabled={isStreamActive}
            title={isStreamActive ? "Cannot create new chat while streaming" : "Start New Chat"}
          >
            + New Chat
          </button>
        </div>
      </div>
      
      <div className="chat-list">
        {chats.map((chat) => (
          <div 
            key={chat.id}
            className={`chat-item ${activeChat === chat.id ? 'active' : ''} ${isStreamActive ? 'disabled' : ''}`}
            onClick={isStreamActive ? undefined : () => onChatSelect(chat.id)}
            style={{ cursor: isStreamActive ? 'not-allowed' : 'pointer' }}
            title={isStreamActive ? "Cannot switch chats while streaming" : ""}
          >
            <div className="chat-item-content">
              <div className="chat-title">
                {editingChatId === chat.id ? (
                  <input
                    type="text"
                    value={editingTitle}
                    onChange={(e) => setEditingTitle(e.target.value)}
                    onBlur={handleTitleSave}
                    onKeyDown={handleKeyPress}
                    autoFocus
                    className="title-edit-input"
                  />
                ) : (
                  <span 
                    onDoubleClick={() => !isStreamActive && handleTitleEdit(chat.id, chat.title || 'New chat')}
                    title="Double-click to edit title"
                  >
                    {chat.title || `New chat`}
                  </span>
                )}
              </div>
              <div className="chat-preview">
                {chat.messages.length > 0 
                  ? chat.messages[0].content.slice(0, 100) + '...'
                  : 'New conversation'
                }
              </div>
              <div className="chat-timestamp">
                {new Date(chat.lastUpdated).toLocaleDateString()}
              </div>
            </div>
            <button 
              className="delete-chat-btn"
              onClick={(e) => {
                e.stopPropagation();
                if (!isStreamActive) {
                  onDeleteChat(chat.id);
                }
              }}
              disabled={isStreamActive}
              title={isStreamActive ? "Cannot delete chat while streaming" : "Delete Chat"}
            >
              ×
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ChatSidebar;
