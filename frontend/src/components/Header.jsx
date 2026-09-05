import React from 'react';

export function Header({ onRunBatch, onResetBatch, loading }) {
  return (
    <header className="top-header">
      <div className="header-inner">
        <div className="header-brand">
          <h1 className="brand-title">AI Revenue Recovery Agent</h1>
          <span className="brand-badge">Mandate Retry + Hinglish PTP</span>
        </div>
        <div className="header-actions">
          <button
            className="btn btn-primary"
            onClick={() => onRunBatch(15)}
            disabled={loading}
          >
            {loading ? 'Processing...' : 'Run Simulation (15 Cases)'}
          </button>
          <button
            className="btn btn-subtle"
            onClick={onResetBatch}
            disabled={loading}
          >
            Reset
          </button>
        </div>
      </div>
    </header>
  );
}
