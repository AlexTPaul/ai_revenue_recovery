import React, { useEffect, useState } from 'react';
import { api } from '../services/api';

export function EscalationQueue({ onRefreshState }) {
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCase, setSelectedCase] = useState(null);
  const [resolutionAction, setResolutionAction] = useState('manual_upi_payment');
  const [amountCollected, setAmountCollected] = useState('');
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const fetchQueue = () => {
    setLoading(true);
    api
      .getEscalationQueue()
      .then((data) => {
        setQueue(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to fetch escalation queue:', err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchQueue();
  }, []);

  const handleResolveSubmit = async (e) => {
    e.preventDefault();
    if (!selectedCase) return;

    setSubmitting(true);
    try {
      await api.resolveEscalation(selectedCase.case_id, {
        action_taken: resolutionAction,
        resolution_notes: notes || 'Resolved via human triage',
        amount_collected: amountCollected ? parseFloat(amountCollected) : 0.0,
      });
      setSelectedCase(null);
      setAmountCollected('');
      setNotes('');
      fetchQueue();
      if (onRefreshState) onRefreshState();
    } catch (err) {
      alert(`Resolution failed: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  const formatINR = (val) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(val || 0);
  };

  return (
    <div className="table-card">
      <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)' }}>
            Human Escalation & Triage Queue
          </h3>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px' }}>
            Cases where automated retries, closed accounts, or broken promises reached regulatory stopping bounds.
          </p>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={fetchQueue} disabled={loading}>
          {loading ? 'Refreshing...' : 'Refresh Queue'}
        </button>
      </div>

      <div className="table-responsive">
        <table className="data-table">
          <thead>
            <tr>
              <th>Case ID & Customer</th>
              <th>Amount</th>
              <th>Initial Failure</th>
              <th>Escalation Rationale</th>
              <th>Escalated At</th>
              <th style={{ textAlign: 'right' }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {queue.length === 0 ? (
              <tr>
                <td colSpan="6" style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)' }}>
                  {loading ? 'Loading escalation queue...' : 'No escalated cases in queue. Run simulation or advance clock to generate.'}
                </td>
              </tr>
            ) : (
              queue.map((item) => (
                <tr key={item.case_id}>
                  <td>
                    <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{item.customer_name}</div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                      {item.customer_phone} &bull; {item.case_id}
                    </div>
                  </td>
                  <td style={{ fontWeight: 600 }}>{formatINR(item.amount)}</td>
                  <td>
                    <span className="reason-pill">{item.failure_reason}</span>
                  </td>
                  <td style={{ maxWidth: '300px' }}>
                    <div style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
                      {item.escalation_reason}
                    </div>
                  </td>
                  <td>
                    <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                      {new Date(item.escalated_at).toLocaleString([], {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </span>
                  </td>
                  <td>
                    <div className="actions-cell" style={{ justifyContent: 'flex-end' }}>
                      <button
                        className="btn btn-primary btn-sm"
                        onClick={() => {
                          setSelectedCase(item);
                          setAmountCollected(item.amount.toString());
                        }}
                      >
                        Resolve Case
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Resolution Modal */}
      {selectedCase && (
        <div className="modal-backdrop" onClick={() => setSelectedCase(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 style={{ fontSize: '15px', fontWeight: 600 }}>Resolve Escalated Case</h3>
              <button className="btn btn-subtle btn-sm" onClick={() => setSelectedCase(null)}>
                Close
              </button>
            </div>
            <form onSubmit={handleResolveSubmit}>
              <div className="modal-body">
                <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                  Customer: <strong>{selectedCase.customer_name}</strong> &bull; Due: <strong>{formatINR(selectedCase.amount)}</strong>
                </div>

                <div className="form-group">
                  <label className="form-label">Resolution Action Taken</label>
                  <select
                    className="select-input"
                    value={resolutionAction}
                    onChange={(e) => setResolutionAction(e.target.value)}
                  >
                    <option value="manual_upi_payment">Collected via Manual UPI / Net Banking</option>
                    <option value="re_mandate_registered">Customer Registered New Mandate</option>
                    <option value="partial_settlement">Agreed to Partial Settlement</option>
                    <option value="written_off_closed">Subscription Cancelled / Account Closed</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Amount Recovered (₹)</label>
                  <input
                    type="number"
                    step="0.01"
                    className="form-input"
                    value={amountCollected}
                    onChange={(e) => setAmountCollected(e.target.value)}
                    placeholder="e.g. 2499.00"
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Agent Resolution Notes</label>
                  <textarea
                    className="form-textarea"
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    placeholder="Enter compliance notes or verification details..."
                  />
                </div>
              </div>
              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-subtle btn-sm"
                  onClick={() => setSelectedCase(null)}
                  disabled={submitting}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary btn-sm" disabled={submitting}>
                  {submitting ? 'Submitting...' : 'Record Resolution'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
