import React from 'react';
import { marked } from 'marked';
import Image from 'next/image';

const ChatMessage = ({ message, isUser }) => {
  const renderMarkdown = (content) => {
    if (!content) return '';
    try {
      return marked.parse(content); 
    } catch (error) {
      console.error('Error parsing markdown:', error);
      return content;
    }
  };

  return (
    <div className={`message-row ${isUser ? 'user' : 'api'}`}>
      {/* Avatar tylko dla API */}
      {!isUser && (
        <div className="message-avatar">
          <Image
            src="/assets/pbots_logo.png"
            alt="logo"
            width={30}
            height={30}
          />
        </div>
      )}
      {/* Dymek */}
      <div className={`message ${isUser ? 'user' : 'api'}`}>
        <span className="tag">{isUser ? 'Użytkownik' : 'PBotS'}</span>
        {isUser ? (
          <div className="message-content">
            {message}
          </div>
        ) : (
          <div 
            className="message-content"
            dangerouslySetInnerHTML={{ __html: renderMarkdown(message) }}
          />
        )}
      </div>
    </div>
  );
};

export default ChatMessage;
