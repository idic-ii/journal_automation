import React from 'react';

export default function LiveDot({ visible }) {
  if (!visible) return null;
  return (
    <div className="live-indicator">
      <span className="live-dot" />
      <span>Recolectando datos…</span>
    </div>
  );
}
