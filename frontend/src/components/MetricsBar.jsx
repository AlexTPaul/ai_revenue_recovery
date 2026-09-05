import React from 'react';

export function MetricsBar({ summary }) {
  const atRisk = summary?.total_at_risk || 0;
  const recovered = summary?.total_recovered || 0;
  const rate = summary?.recovery_rate_pct || 0;
  const breakdown = summary?.status_breakdown || {};

  const formatINR = (val) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(val);
  };

  return (
    <div className="metrics-grid">
      <div className="metric-card">
        <span className="metric-title">Total Value At Risk</span>
        <div className="metric-value-row">
          <span className="metric-value">{formatINR(atRisk)}</span>
          <span className="metric-sub">{summary?.total_cases || 0} Total Cases</span>
        </div>
      </div>

      <div className="metric-card">
        <span className="metric-title">Recovered Revenue</span>
        <div className="metric-value-row">
          <span className="metric-value" style={{ color: '#34d399' }}>
            {formatINR(recovered)}
          </span>
          <span className="metric-sub">{rate}% Rate</span>
        </div>
        <div className="progress-bar-bg">
          <div className="progress-bar-fill" style={{ width: `${Math.min(100, rate)}%` }}></div>
        </div>
      </div>

      <div className="metric-card">
        <span className="metric-title">Active Retry Queue</span>
        <div className="metric-value-row">
          <span className="metric-value" style={{ color: '#38bdf8' }}>
            {breakdown.pending_retry || 0}
          </span>
          <span className="metric-sub">Scheduled</span>
        </div>
      </div>

      <div className="metric-card">
        <span className="metric-title">Promise-to-Pay (PTP)</span>
        <div className="metric-value-row">
          <span className="metric-value" style={{ color: '#fbbf24' }}>
            {breakdown.ptp_open || 0}
          </span>
          <span className="metric-sub">Negotiations</span>
        </div>
      </div>

      <div className="metric-card">
        <span className="metric-title">Escalated to Human</span>
        <div className="metric-value-row">
          <span className="metric-value" style={{ color: '#f87171' }}>
            {breakdown.escalated || 0}
          </span>
          <span className="metric-sub">Handoffs</span>
        </div>
      </div>
    </div>
  );
}
