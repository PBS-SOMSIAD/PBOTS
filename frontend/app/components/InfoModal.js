'use client';

import React from 'react';

const InfoModal = ({ onClose }) => {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close-btn" onClick={onClose}>
          &times;
        </button>
        <h2>Instrukcja</h2>
        <p>Witaj w PBotŚ! Oto jak możesz z niego korzystać:</p>
        <ul>
          <li>Tu będzie Instrukcja</li>
        </ul>
      </div>
    </div>
  );
};

export default InfoModal;