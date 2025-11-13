import React, { useState } from 'react';
import Image from 'next/image';

const ChatForm = ({ onSubmit, isLoading, onStop }) => {
  const [question, setQuestion] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (isLoading) {
      onStop();
      return;
    }

    if (isLoading) {
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
        placeholder="Zadaj pytanie dotyczące Politechniki Bydgoskiej..."
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