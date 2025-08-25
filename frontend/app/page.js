'use client';

import React, { useState, useEffect, useRef } from 'react';
import ChatContainer from './components/ChatContainer';
import ChatForm from './components/ChatForm';
import Image from 'next/image';
import InfoModal from './components/InfoModal'; 

export default function Home() {
  const [chatStarted, setChatStarted] = useState(false);
  const [showTitleOnBar, setShowTitleOnBar] = useState(false);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleFirstSubmit = async (question) => {
    if (!chatStarted) {
      setChatStarted(true);
      setShowTitleOnBar(true);
    }

    setIsLoading(true);
    const newMessages = [...messages, { content: question, isUser: true }];
    setMessages(newMessages);

    try {
      const response = await fetch('/api/ask/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      });

      if (!response.ok || !response.body) {
        throw new Error('Network response was not ok.');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let apiMessageContent = '';

      setMessages((prevMessages) => [
        ...prevMessages,
        { content: '', isUser: false },
      ]);

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        apiMessageContent += chunk;

        setMessages((prevMessages) => {
          const updatedMessages = [...prevMessages];
          updatedMessages[updatedMessages.length - 1].content = apiMessageContent;
          return updatedMessages;
        });
      }
    } catch (error) {
      console.error('Error fetching stream:', error);
      setMessages((prevMessages) => [
        ...prevMessages,
        { content: 'Przepraszam, wystąpił błąd.', isUser: false },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="page">
      <div className="red-bar">
        <Image
          src="/assets/info_icon.png"
          alt="Info Icon"
          width={50}
          height={50}
          className="icon"
          onClick={() => setIsModalOpen(true)}
        />
        {showTitleOnBar && <span className="bar-title">PBotŚ</span>}
      </div>

      {!chatStarted ? (
        <>
          <header>
            <Image
              src="/assets/pbots_logo.png"
              alt="PBOTS Logo"
              width={120}
              height={120}
            />
            <h1>PBotŚ</h1>
          </header>
          <p className="prompt-text">CZEŚĆ, JAK MOGĘ CI POMÓC?</p>
          <ChatForm onSubmit={handleFirstSubmit} isLoading={isLoading} />
        </>
      ) : (
        <div className="chat-view">
          <ChatContainer messages={messages} />
          <ChatForm onSubmit={handleFirstSubmit} isLoading={isLoading} />
        </div>
      )}

      {isModalOpen && <InfoModal onClose={() => setIsModalOpen(false)} />}
    </div>
  );
}
