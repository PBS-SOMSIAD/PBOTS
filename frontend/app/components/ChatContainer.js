'use client';

import React, { useState, useRef, useEffect } from 'react';
import ChatMessage from './ChatMessage';
import ChatForm from './ChatForm';

const ChatContainer = () => {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesRef = useRef(null);

  // Auto-scroll on new messages
  useEffect(() => {
    const el = messagesRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages]);

  const streamResponse = async (question) => {
    // Add user message
    setMessages(prev => [...prev, { content: question, isUser: true }]);
    setIsLoading(true);
    
    // Add placeholder for response
    const responseId = Date.now().toString();
    setMessages(prev => [...prev, { 
      id: responseId, 
      content: '⏳ Checking if message is appropriate...', 
      isUser: false 
    }]);
    
    try {
      const response = await fetch('/api/ask/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question })
      });
      
      if (!response.ok) throw new Error(`Error ${response.status}`);
      
      // Clear placeholder and start streaming
      setMessages(prev => prev.map(msg => 
        msg.id === responseId ? { ...msg, content: '' } : msg
      ));
      
      // Process the stream
      let text = '';
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        text += decoder.decode(value, { stream: true });
        setMessages(prev => prev.map(msg => 
          msg.id === responseId ? { ...msg, content: text } : msg
        ));
      }
    } catch (error) {
      setMessages(prev => prev.map(msg => 
        msg.id === responseId ? { 
          ...msg, 
          content: `⚠️ Error: ${error.message}` 
        } : msg
      ));
    } finally {
      setIsLoading(false);
    }
  };

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
      <ChatForm onSubmit={streamResponse} isLoading={isLoading} />
    </div>
  );
};

export default ChatContainer;
