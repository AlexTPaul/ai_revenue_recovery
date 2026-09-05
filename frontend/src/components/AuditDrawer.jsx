import React, { useEffect, useState } from 'react';
import { api } from '../services/api';

export function AuditDrawer({ attemptId, onClose, onOpenChat }) {
  const [caseDetail, setCaseDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!attemptId) return;
    setLoading(true);
    setError(null);
    api
      .getCaseDetail(attemptId)
      .then((data) => {
        setCaseDetail(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [attemptId]);

  if (!attemptId) return null;

  const formatINR = (val) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(val || 0);
  };

  const formatTime = (ts) => {
    if (!ts) return '-';
    return new Date(ts).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <div className="drawer-panel" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-header">
          <div>
            <h2 className="drawer-title">Compliance Audit Trail</h2>
            <div className="drawer-subtitle">
              Case #{attemptId} &bull; {caseDetail?.case?.customer_name || 'Loading...'}
            </div>
          </div>
          <button className="btn btn-subtle btn-sm" onClick={onClose}>
            Close
          </button>
        </div>

        <div className="drawer-body">
          {loading ? (
            <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '32px' }}>
              Loading audit logs...
            </div>
          ) : error ? (
            <div style={{ color: 'var(--danger)', padding: '16px' }}>Error: {error}</div>
          ) : (
            <div>
              {/* Case Summary Card */}
              <div
                style={{
                  backgroundColor: 'var(--bg-card)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  padding: '14px 16px',
                  marginBottom: '24px',
                  display: 'grid',
                  gridTemplateColumns: 'repeat(2, 1fr)',
                  gap: '12px',
                  fontSize: '12px',
                }}
              >
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Customer:</span>{' '}
                  <strong style={{ color: 'var(--text-primary)' }}>{caseDetail?.case?.customer_name}</strong>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Amount:</span>{' '}
                  <strong style={{ color: 'var(--text-primary)' }}>{formatINR(caseDetail?.case?.amount)}</strong>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Failure Reason:</span>{' '}
                  <span className="reason-pill">{caseDetail?.case?.failure_reason}</span>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Salary Credit:</span>{' '}
                  <span style={{ color: 'var(--text-secondary)' }}>Day {caseDetail?.case?.salary_credit_day} of month</span>
                </div>
              </div>

              <div style={{ marginBottom: '16px', fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
                Chronological Decision Trail
              </div>

              {/* Timeline */}
              <div className="timeline">
                {caseDetail?.audit_trail?.map((log) => {
                  const isRecovered = log.action === 'recovered' || log.outcome === 'success';
                  const isEscalated = log.action === 'escalated';

                  let dotClass = '';
                  if (isRecovered) dotClass = 'success';
                  if (isEscalated) dotClass = 'danger';

                  return (
                    <div key={log.id} className="timeline-item">
                      <div className={`timeline-dot ${dotClass}`}></div>
                      <div className="timeline-header">
                        <span className="timeline-action">
                          {log.action.replace(/_/g, ' ').toUpperCase()}
                        </span>
                        <span className="timeline-time">{formatTime(log.timestamp)}</span>
                      </div>
                      <div className="timeline-card">
                        <div>{log.reasoning}</div>
                        {log.amount_recovered && (
                          <div style={{ marginTop: '6px', color: '#34d399', fontWeight: 600 }}>
                            Amount Recovered: {formatINR(log.amount_recovered)}
                          </div>
                        )}
                        <div style={{ marginTop: '4px', fontSize: '10px', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                          ID: {log.id} &bull; Entity: {log.entity_type} ({log.entity_id})
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        <div className="drawer-footer" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          {caseDetail?.case?.active_promise_id ? (
            <button
              className="btn btn-primary btn-sm"
              onClick={() => {
                onClose();
                onOpenChat(caseDetail.case.active_promise_id);
              }}
            >
              Open PTP Chat Drawer
            </button>
          ) : (
            <div></div>
          )}
          <button className="btn btn-secondary btn-sm" onClick={onClose}>
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
