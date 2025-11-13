'use client';

import React, { useState, useEffect, useRef } from 'react';
import ChatContainer from './components/ChatContainer';
import ChatForm from './components/ChatForm';
import Image from 'next/image';
import InfoModal from './components/InfoModal'; 
import WarningPopup from './components/WarningPopup';

export default function Home() {
  const [chatStarted, setChatStarted] = useState(false);
  const [showTitleOnBar, setShowTitleOnBar] = useState(false);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // AbortController do przerywania żądań
  const abortControllerRef = useRef(null);
  // Ref do śledzenia czy już zatrzymaliśmy "myślenie"
  const hasStoppedThinkingRef = useRef(false);

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setIsLoading(false);
      setIsThinking(false);
      hasStoppedThinkingRef.current = false;

      setMessages((prevMessages) => {
        const updatedMessages = [...prevMessages];

        const lastMessage = updatedMessages[updatedMessages.length - 1];
        const hasBotMessage = lastMessage && !lastMessage.isUser;

        if (hasBotMessage) {
          if (!lastMessage.content.includes('[Odpowiedź przerwana przez użytkownika]')) {
            if (lastMessage.content.trim() === '') {
              lastMessage.content = '[Odpowiedź przerwana przez użytkownika]';
            } else {
              lastMessage.content += '\n\n[Odpowiedź przerwana przez użytkownika]';
            }
          }
        } else {
          updatedMessages.push({
            content: '[Odpowiedź przerwana przez użytkownika]',
            isUser: false
          });
        }

        return updatedMessages;
      });
    }
  };

  const handleSubmit = async (question) => {
    if (!chatStarted) {
      setChatStarted(true);
      setShowTitleOnBar(true);
    }

    setIsLoading(true);
    setIsThinking(true);
    hasStoppedThinkingRef.current = false;
    const newMessages = [...messages, { content: question, isUser: true }];
    setMessages(newMessages);

    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch('/api/ask/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
        signal: abortControllerRef.current.signal
      });

      if (!response.ok || !response.body) {
        throw new Error('Network response was not ok.');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let apiMessageContent = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        apiMessageContent += chunk;

        if (apiMessageContent.length > 0 && !hasStoppedThinkingRef.current) {
          setIsThinking(false);
          hasStoppedThinkingRef.current = true;

          setMessages((prevMessages) => [
            ...prevMessages,
            { content: apiMessageContent, isUser: false },
          ]);
        } else if (hasStoppedThinkingRef.current) {
          setMessages((prevMessages) => {
            const updatedMessages = [...prevMessages];
            updatedMessages[updatedMessages.length - 1].content = apiMessageContent;
            return updatedMessages;
          });
        }
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        console.log('Żądanie zostało przerwane przez użytkownika');
        return;
      }

      console.error('Error fetching stream:', error);

      setIsThinking(false);
      setMessages((prevMessages) => [
        ...prevMessages,
        { content: 'Przepraszam, wystąpił błąd.', isUser: false },
      ]);
    } finally {
      setIsLoading(false);
      setIsThinking(false);
      hasStoppedThinkingRef.current = false;
      abortControllerRef.current = null;
    }
  };

  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

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
          <ChatForm
            onSubmit={handleSubmit}
            isLoading={isLoading}
            onStop={handleStop}
          />
        </>
      ) : (
        <div className="chat-view">
          <ChatContainer
            messages={messages}
            isLoading={isLoading}
            isThinking={isThinking}
          />
          <ChatForm
            onSubmit={handleSubmit}
            isLoading={isLoading}
            onStop={handleStop}
          />
        </div>
      )}

      {isModalOpen && <InfoModal onClose={() => setIsModalOpen(false)} />}
      <WarningPopup />
    </div>
  );
}