'use client';

import React, { useEffect, useRef } from 'react';
import ChatMessage from './ChatMessage';

const ChatContainer = ({ messages, isLoading, isThinking }) => {
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
        {isThinking && ( // Użyj isThinking zamiast isLoading
          <ChatMessage
            message=""
            isUser={false}
            isLoading={true} // To kontroluje wyświetlanie animowanych kropek
          />
        )}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
};

export default ChatContainer;