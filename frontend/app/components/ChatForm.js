import React, { useState } from 'react';

const ChatForm = ({ onSubmit, isLoading, onCancel }) => {
  const [question, setQuestion] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
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
        placeholder="Ask a question about D&D..."
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        disabled={isLoading}
      />
      <button type="submit" disabled={isLoading || !question.trim()}>
        {isLoading ? 'Thinking...' : 'Ask'}
      </button>
      {isLoading && onCancel && (
        <button type="button" onClick={onCancel} className="cancel-btn">
          Cancel
        </button>
      )}
    </form>
  );
};

export default ChatForm;
