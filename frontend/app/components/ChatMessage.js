import React from 'react';
import { marked } from 'marked';
import Image from 'next/image';
import DOMPurify from 'dompurify';

const ChatMessage = ({ message, isLoading, isUser }) => {
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
            width={52}
            height={52}
          />
        </div>
      )}
      <div className={`message ${isUser ? 'user' : 'api'}`}>
        <span className="tag">{isUser ? 'Użytkownik' : 'PBotŚ'}</span>
        <div className="message-content">
          {isLoading && !isUser ? (
            <div className="dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
          ) : isUser ? (
            message
          ) : (
            <div
              dangerouslySetInnerHTML={{ __html: renderMarkdown(message) }}
            />
          )}
        </div>
      </div>

      {isUser && (
        <div className="message-avatar">
          <Image
            src="/assets/user_icon.png"
            alt="user avatar"
            width={40}
            height={40}
          />
        </div>
      )}
    </div>
  );
};

export default ChatMessage;
