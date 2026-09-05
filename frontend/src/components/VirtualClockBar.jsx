import React from 'react';

export function VirtualClockBar({ clock, onFastForward, onResetClock, loading }) {
  return (
    <div className="clock-bar">
      <div className="clock-info">
        <span className="clock-label">Virtual Simulation Clock</span>
        <div className="clock-time-display">
          <div className="clock-indicator"></div>
          <span>{clock?.formatted_time || 'Loading clock...'}</span>
        </div>
      </div>

      <div className="clock-controls">
        <span className="clock-label" style={{ marginRight: '4px' }}>Fast-Forward:</span>
        <button
          className="btn btn-secondary btn-sm"
          onClick={() => onFastForward(1, 0)}
          disabled={loading}
        >
          +1 Day
        </button>
        <button
          className="btn btn-secondary btn-sm"
          onClick={() => onFastForward(2, 0)}
          disabled={loading}
          title="Advances by 2 days (salary buffer evaluation)"
        >
          +2 Days (Salary Buffer)
        </button>
        <button
          className="btn btn-secondary btn-sm"
          onClick={() => onFastForward(3, 0)}
          disabled={loading}
        >
          +3 Days
        </button>
        <button
          className="btn btn-secondary btn-sm"
          onClick={() => onFastForward(7, 0)}
          disabled={loading}
        >
          +7 Days
        </button>
        <button
          className="btn btn-subtle btn-sm"
          onClick={onResetClock}
          disabled={loading}
        >
          Reset Clock (Sep 01)
        </button>
      </div>
    </div>
  );
}
