'use client';

import React, { useRef, useEffect } from 'react';
import ChatMessage from './ChatMessage';
import ChatForm from './ChatForm';

const ChatContainer = ({ messages = [], isLoading = false, onSubmit, onCancel }) => {
  const messagesRef = useRef(null);

  // Auto-scroll on new messages
  useEffect(() => {
    const el = messagesRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages]);

  return (
    <div id="chat-container">
      <div id="messages" ref={messagesRef}>
        {messages.map((msg, index) => (
          <ChatMessage
            key={index}
            message={msg.content}
            isUser={msg.isUser}
          />
        ))}
      </div>
      <ChatForm 
        onSubmit={onSubmit} 
        isLoading={isLoading} 
        onCancel={onCancel} 
      />
    </div>
  );
};

export default ChatContainer;
