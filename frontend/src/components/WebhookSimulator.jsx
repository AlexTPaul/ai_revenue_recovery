import React, { useState } from 'react';
import { api } from '../services/api';

export function WebhookSimulator({ onRefreshState }) {
  const [eventType, setEventType] = useState('payment_link.paid');
  const [plinkId, setPlinkId] = useState('plink_rzp_001');
  const [amount, setAmount] = useState('4999.00');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleFireWebhook = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);

    let payload = {};
    if (eventType === 'payment_link.paid') {
      payload = {
        event: 'payment_link.paid',
        payload: {
          payment_link: {
            entity: {
              id: plinkId,
              amount: parseFloat(amount) * 100,
              status: 'paid',
            },
          },
        },
      };
    } else if (eventType === 'subscription.charged') {
      payload = {
        event: 'subscription.charged',
        payload: {
          subscription: {
            entity: {
              id: 'sub_rzp_001',
              status: 'active',
            },
          },
        },
      };
    }

    try {
      const res = await api.simulateRazorpayWebhook(payload);
      setResult({ success: true, data: res });
      if (onRefreshState) onRefreshState();
    } catch (err) {
      setResult({ success: false, error: err.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="table-card" style={{ padding: '24px' }}>
      <div style={{ marginBottom: '20px' }}>
        <h3 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-primary)' }}>
          Razorpay Webhook Simulator
        </h3>
        <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
          Test incoming webhook events from Razorpay payment gateway to verify automated revenue reconciliation.
        </p>
      </div>

      <form onSubmit={handleFireWebhook} style={{ maxWidth: '600px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div className="form-group">
          <label className="form-label">Webhook Event Type</label>
          <select
            className="select-input"
            value={eventType}
            onChange={(e) => setEventType(e.target.value)}
          >
            <option value="payment_link.paid">payment_link.paid (Promise-to-Pay Settled)</option>
            <option value="subscription.charged">subscription.charged (Mandate Auto-Debit Cleared)</option>
          </select>
        </div>

        {eventType === 'payment_link.paid' && (
          <>
            <div className="form-group">
              <label className="form-label">Payment Link ID</label>
              <input
                type="text"
                className="form-input"
                value={plinkId}
                onChange={(e) => setPlinkId(e.target.value)}
                placeholder="plink_xxxx"
              />
            </div>
            <div className="form-group">
              <label className="form-label">Amount Paid (₹)</label>
              <input
                type="number"
                step="0.01"
                className="form-input"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="4999.00"
              />
            </div>
          </>
        )}

        <button type="submit" className="btn btn-primary" style={{ alignSelf: 'flex-start' }} disabled={loading}>
          {loading ? 'Sending Webhook...' : 'Fire Simulated Webhook'}
        </button>
      </form>

      {result && (
        <div
          style={{
            marginTop: '20px',
            padding: '14px 16px',
            backgroundColor: 'var(--bg-card)',
            border: `1px solid ${result.success ? 'var(--success-border)' : 'var(--danger-border)'}`,
            borderRadius: 'var(--radius-md)',
            fontSize: '12px',
            fontFamily: 'monospace',
          }}
        >
          <strong style={{ color: result.success ? '#34d399' : '#f87171' }}>
            {result.success ? 'Webhook Processed Successfully' : 'Webhook Failed'}
          </strong>
          <pre style={{ marginTop: '8px', color: 'var(--text-secondary)', overflowX: 'auto' }}>
            {JSON.stringify(result.data || result.error, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
