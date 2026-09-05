import React, { useState } from 'react';

export function CaseTable({ cases, onSelectAudit, onOpenChat, loading }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [reasonFilter, setReasonFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');

  const filteredCases = cases.filter((c) => {
    const matchesSearch =
      c.customer_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.customer_phone.includes(searchTerm) ||
      c.id.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesReason = reasonFilter === 'all' || c.failure_reason === reasonFilter;
    const matchesStatus = statusFilter === 'all' || c.status === statusFilter;

    return matchesSearch && matchesReason && matchesStatus;
  });

  const formatINR = (val) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(val);
  };

  const getStatusBadge = (status, nextAction) => {
    if (status === 'success') {
      return <span className="badge badge-success">Recovered</span>;
    }
    if (nextAction === 'escalate' || status === 'escalated') {
      return <span className="badge badge-danger">Escalated</span>;
    }
    if (nextAction === 'route_to_ptp' || status === 'ptp_open') {
      return <span className="badge badge-warning">PTP Active</span>;
    }
    if (status === 'pending') {
      return <span className="badge badge-info">Retry Scheduled</span>;
    }
    return <span className="badge badge-neutral">{status}</span>;
  };

  const formatScheduledDate = (dateStr) => {
    if (!dateStr) return '-';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="table-card">
      <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-subtle)' }}>
        <div className="filters-row" style={{ justifyContent: 'space-between', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
            <input
              type="text"
              placeholder="Search customer, phone, or case ID..."
              className="search-input"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            <select
              className="select-input"
              value={reasonFilter}
              onChange={(e) => setReasonFilter(e.target.value)}
            >
              <option value="all">All Failure Reasons</option>
              <option value="insufficient_funds">Insufficient Funds</option>
              <option value="bank_timeout">Bank Timeout</option>
              <option value="technical_decline">Technical Decline</option>
              <option value="mandate_expired">Mandate Expired</option>
              <option value="account_closed">Account Closed</option>
            </select>
            <select
              className="select-input"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="all">All Statuses</option>
              <option value="pending">Pending</option>
              <option value="success">Success / Recovered</option>
              <option value="failed">Failed</option>
            </select>
          </div>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            Showing {filteredCases.length} of {cases.length} cases
          </span>
        </div>
      </div>

      <div className="table-responsive">
        <table className="data-table">
          <thead>
            <tr>
              <th>Customer & Mandate</th>
              <th>Amount</th>
              <th>Failure Diagnosis</th>
              <th>Salary Day</th>
              <th>Attempt</th>
              <th>Scheduled Time / Action</th>
              <th>Status</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredCases.length === 0 ? (
              <tr>
                <td colSpan="8" style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)' }}>
                  {loading ? 'Loading cases...' : 'No recovery cases found. Click "Run Simulation" above to seed.'}
                </td>
              </tr>
            ) : (
              filteredCases.map((c) => (
                <tr key={c.id}>
                  <td>
                    <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{c.customer_name}</div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                      {c.customer_phone} &bull; {c.id}
                    </div>
                  </td>
                  <td style={{ fontWeight: 600 }}>{formatINR(c.amount)}</td>
                  <td>
                    <span className="reason-pill">{c.failure_reason}</span>
                  </td>
                  <td>
                    <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                      Day {c.salary_credit_day}
                    </span>
                  </td>
                  <td>
                    <span style={{ fontSize: '12px', fontFamily: 'monospace' }}>
                      #{c.attempt_number}
                    </span>
                  </td>
                  <td>
                    <div style={{ fontSize: '12px', color: 'var(--text-primary)' }}>
                      {c.next_action === 'retry_scheduled'
                        ? formatScheduledDate(c.scheduled_at)
                        : c.next_action || '-'}
                    </div>
                    {c.decision_explanation && (
                      <div
                        style={{
                          fontSize: '11px',
                          color: 'var(--text-muted)',
                          maxWidth: '240px',
                          whiteSpace: 'nowrap',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                        }}
                        title={c.decision_explanation}
                      >
                        {c.decision_explanation}
                      </div>
                    )}
                  </td>
                  <td>{getStatusBadge(c.status, c.next_action)}</td>
                  <td>
                    <div className="actions-cell" style={{ justifyContent: 'flex-end' }}>
                      {c.active_promise_id && (
                        <button
                          className="btn btn-secondary btn-sm"
                          onClick={() => onOpenChat(c.active_promise_id)}
                          title="Open Hinglish PTP Chat Drawer"
                        >
                          PTP Chat
                        </button>
                      )}
                      <button
                        className="btn btn-subtle btn-sm"
                        onClick={() => onSelectAudit(c.id)}
                        title="View Compliance Audit Trail"
                      >
                        Audit Trail
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
