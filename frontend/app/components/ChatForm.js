import React, { useState } from 'react';
import Image from 'next/image';

const ChatForm = ({ onSubmit, isLoading, onStop }) => {
  const [question, setQuestion] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (isLoading) {
      // Jeśli ładuje, wywołaj funkcję stop
      onStop();
      return;
    }

    if (isLoading) {
      // Jeśli ładuje, wywołaj funkcję stop
      onStop();
      return;
    }

    const trimmed = question.trim();
    if (trimmed) {
      onSubmit(trimmed);
      setQuestion('');
    }
  };

  return (
    <form id="chat-form" onSubmit={handleSubmit}>
      <input
        type="text"
        id="question"
        placeholder="ZADAJ PYTANIE ..."
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        disabled={isLoading}
      />
      <button type="submit" disabled={!isLoading && !question.trim()}>
        {isLoading ? (
          <Image
            src="/assets/stop_icon.png"
            alt="stopIcon"
            width={50}
            height={50}
          />
        ) : (
          <Image
            src="/assets/arrow_up.png"
            alt="arrowIcon"
            width={50}
            height={50}
          />
        )}
      </button>
    </form>
  );
};

export default ChatForm;