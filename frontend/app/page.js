'use client';

import React, { useState, useEffect, useRef } from 'react';
import ChatContainer from './components/ChatContainer'; // Zmienimy jego rolę
import ChatForm from './components/ChatForm';
import Image from 'next/image';

export default function Home() {
  const [chatStarted, setChatStarted] = useState(false);
  const [showTitleOnBar, setShowTitleOnBar] = useState(false);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

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
          width={40}
          height={40}
          className="icon"
        />
        {showTitleOnBar && <span className="bar-title">PBotS</span>}
      </div>

      {/* Warunkowe wyświetlanie: albo nagłówek, albo czat */}
      {!chatStarted ? (
        <header>
          <Image
            src="/assets/pbots_logo.png"
            alt="PBOTS Logo"
            width={120} /* Zwiększono rozmiar logo */
            height={120}
          />
          <h1>PBotS</h1>
          {/* Usunięto <p>Zadaj pytanie!</p> stąd */}
        </header>
      ) : (
        <ChatContainer messages={messages} />
      )}

      {/* Krok 1: Dodaj napis "Zadaj pytanie!" tutaj, widoczny tylko przed startem czatu */}
      {!chatStarted && (
        <p className="prompt-text">CZEŚĆ, JAK MOGE CI POMOC?</p>
      )}

      {/* Formularz jest na dole */}
      <ChatForm onSubmit={handleFirstSubmit} isLoading={isLoading} />
    </div>
  );
}
