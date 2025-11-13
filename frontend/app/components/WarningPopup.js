'use client';

import React, { useState } from 'react';
import Image from 'next/image';

const WarningPopup = () => {
  const [isVisible, setIsVisible] = useState(true);

  if (!isVisible) return null;

  return (
    <div className="warning-popup">
      <button
        className="warning-popup-close"
        onClick={() => setIsVisible(false)}
        aria-label="Zamknij ostrzeżenie"
      >
        ×
      </button>
      <div className="warning-popup-icon">⚠️</div>
      <div className="warning-popup-content">
        <h3>Ważne!</h3>
        <p>
          PBotŚ może czasami generować niedokładne lub niepełne informacje.
          Zalecamy weryfikację podanych danych z oficjalnymi źródłami Politechniki Bydgoskiej.
        </p>
      </div>
    </div>
  );
};

export default WarningPopup;