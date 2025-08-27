'use client';

import React, { useEffect, useRef } from 'react';
import ChatMessage from './ChatMessage';

const ChatContainer = ({ messages, isLoading}) => {
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    <div id="chat-container">
      <div id="messages">
        {messages.map((msg, index) => (
          <ChatMessage
            key={index}
            message={msg.content}
            isUser={msg.isUser}
            isLoading={false}
          />
        ))}
        {isLoading && (
          <ChatMessage
            message=""
            isUser={false}
            isLoading={true}
          />
        )}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
};

export default ChatContainer;
