import React from 'react';
import { marked } from 'marked';
import Image from 'next/image';
import DOMPurify from 'dompurify';

const ChatMessage = ({ message, isUser }) => {
  const renderMarkdown = (content) => {
    if (!content) return '';
    try {
      const html = marked.parse(content); 
      return DOMPurify.sanitize(html, { USE_PROFILES: { html: true } });
    } catch (error) {
      console.error('Error parsing markdown:', error);
      return DOMPurify.sanitize(content, { USE_PROFILES: { html: true } });
    }
  };

  return (
    <div className={`message-row ${isUser ? 'user' : 'api'}`}>
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
        <span className="tag">{isUser ? 'Użytkownik' : 'PBotŚ'}</span>
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
