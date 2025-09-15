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
            <li><b>1. Zadaj pytanie</b> – wpisz w polu czatu to, co chcesz wiedzieć o Politechnice Bydgoskiej.</li>
            <li><b>2. Wyślij</b> – naciśnij Enter lub kliknij przycisk.</li>
            <li><b>3. Otrzymaj odpowiedź</b> – bot wygeneruje ją korzystając z bazy wiedzy PBŚ.</li>
            <li><b>4. Kontynuuj rozmowę</b> – możesz zadawać kolejne pytania, a bot zapamięta kontekst.</li>
        </ul>
          <p><i>Wskazówka: zadawaj pytania krótko i konkretnie, np. „Jakie są godziny centralnego dziekanatu?”</i></p>
      </div>
    </div>
  );
};

export default InfoModal;