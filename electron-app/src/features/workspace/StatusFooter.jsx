import React from 'react';

export default function StatusFooter({ status }) {
  return (
    <footer className="footer-strip">
      <span>{status}</span>
      <span>Electron ↔ Python bridge remains the only execution path for simulation runs.</span>
    </footer>
  );
}
