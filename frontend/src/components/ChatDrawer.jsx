import React, { useEffect, useState, useRef } from 'react';
import { api } from '../services/api';

export function ChatDrawer({ promiseId, onClose, onRefreshState }) {
  const [history, setHistory] = useState(null);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState(null);
  const [lastExtraction, setLastExtraction] = useState(null);
  const [language, setLanguage] = useState('hinglish'); // 'hinglish' | 'english'
  const messagesEndRef = useRef(null);

  const fetchHistory = () => {
    if (!promiseId) return;
    setLoading(true);
    api
      .getChatHistory(promiseId)
      .then((data) => {
        setHistory(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchHistory();
  }, [promiseId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [history?.messages]);

  if (!promiseId) return null;

  const handleSendMessage = async (textToSend) => {
    const text = textToSend || inputMessage;
    if (!text.trim() || sending) return;

    setSending(true);
    setError(null);
    try {
      const res = await api.sendMessage(promiseId, text, language);
      setInputMessage('');
      setLastExtraction(res.extracted_data);
      await fetchHistory();
      if (onRefreshState) onRefreshState();
    } catch (err) {
      setError(err.message);
    } finally {
      setSending(false);
    }
  };

  const handleSimulatePayment = async () => {
    if (!history?.payment_link) return;
    setSending(true);
    try {
      const plinkId = history.payment_link.split('/').pop();
      await api.simulateRazorpayWebhook({
        event: 'payment_link.paid',
        payload: {
          payment_link: {
            entity: {
              id: plinkId.startsWith('plink_') ? plinkId : `plink_${plinkId}`,
              amount: (history.amount || 1000) * 100,
              status: 'paid',
            },
          },
        },
      });
      await fetchHistory();
      if (onRefreshState) onRefreshState();
    } catch (err) {
      setError(err.message);
    } finally {
      setSending(false);
    }
  };

  const quickRepliesHinglish = [
    { label: 'Definite Date (Somvar)', text: 'Agle somvar pakka pay kar dunga' },
    { label: 'Payday (5th Tareekh)', text: 'Bhai 5 tareekh ko salary aayegi tab pakka dunga' },
    { label: 'Vague / Ambiguous (Gate Test)', text: 'Jaldi hi de dunga bhai thoda time do' },
    { label: 'Explicit Refusal (Escalation Test)', text: 'Nahi dunga, subscription cancel karo' },
  ];

  const quickRepliesEnglish = [
    { label: 'Definite Date (Next Monday)', text: 'I will pay next Monday for sure' },
    { label: 'Payday (5th of Month)', text: 'I will pay on the 5th once my salary is credited' },
    { label: 'Vague / Ambiguous (Gate Test)', text: 'I will pay soon, please give me a few days' },
    { label: 'Explicit Refusal (Escalation Test)', text: 'I will not pay, please cancel my subscription' },
  ];

  const quickReplies = language === 'english' ? quickRepliesEnglish : quickRepliesHinglish;

  const formatINR = (val) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(val || 0);
  };

  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <div className="drawer-panel" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-header">
          <div>
            <h2 className="drawer-title">Promise-to-Pay (PTP) Chat</h2>
            <div className="drawer-subtitle">
              {history?.customer_name || 'Customer'} &bull; {history?.customer_phone} &bull; Due: {formatINR(history?.amount)}
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div className="tabs-nav" style={{ padding: '2px' }}>
              <button
                className={`tab-btn ${language === 'hinglish' ? 'active' : ''}`}
                style={{ fontSize: '11px', padding: '3px 8px' }}
                onClick={() => setLanguage('hinglish')}
                type="button"
              >
                Hinglish
              </button>
              <button
                className={`tab-btn ${language === 'english' ? 'active' : ''}`}
                style={{ fontSize: '11px', padding: '3px 8px' }}
                onClick={() => setLanguage('english')}
                type="button"
              >
                English
              </button>
            </div>
            <button className="btn btn-subtle btn-sm" onClick={onClose}>
              Close
            </button>
          </div>
        </div>


        <div className="drawer-body chat-container">
          {/* Status & Commitment Info */}
          <div
            style={{
              backgroundColor: 'var(--bg-card)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              padding: '10px 14px',
              marginBottom: '16px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              fontSize: '12px',
            }}
          >
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Status:</span>{' '}
              <strong style={{ color: history?.status === 'kept' ? '#34d399' : history?.status === 'escalated' ? '#f87171' : '#fbbf24' }}>
                {history?.status?.toUpperCase()}
              </strong>
            </div>
            {history?.promised_date && (
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Promised Date:</span>{' '}
                <strong style={{ color: '#38bdf8' }}>{history.promised_date}</strong>
              </div>
            )}
          </div>

          {/* Conversation History */}
          <div className="chat-history">
            {loading ? (
              <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '24px' }}>
                Loading conversation...
              </div>
            ) : (
              history?.messages?.map((msg) => (
                <div key={msg.id} className={`chat-bubble ${msg.sender}`}>
                  <div>{msg.message}</div>
                  <div className="chat-meta">
                    <span>{msg.sender === 'agent' ? 'AI Agent' : 'Customer'}</span>
                    <span>{new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                  </div>
                </div>
              ))
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Payment Link Card if generated */}
          {history?.payment_link && history?.status !== 'kept' && (
            <div className="payment-box">
              <div className="payment-box-title">Razorpay Trackable Payment Link Issued</div>
              <div className="payment-box-url">{history.payment_link}</div>
              <button
                className="btn btn-primary btn-sm"
                onClick={handleSimulatePayment}
                disabled={sending}
                style={{ alignSelf: 'flex-start' }}
              >
                Simulate Customer Payment
              </button>
            </div>
          )}

          {error && <div style={{ color: 'var(--danger)', fontSize: '12px', marginTop: '8px' }}>{error}</div>}
        </div>

        <div className="drawer-footer">
          {/* Quick reply chips */}
          <div className="quick-chips-wrapper">
            <div className="quick-chips-label">Quick Test Inputs:</div>
            <div className="quick-chips">
              {quickReplies.map((q, idx) => (
                <button
                  key={idx}
                  className="chip-btn"
                  onClick={() => handleSendMessage(q.text)}
                  disabled={sending || history?.status === 'kept' || history?.status === 'escalated'}
                >
                  {q.label}
                </button>
              ))}
            </div>
          </div>

          {/* Input field */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="chat-input-row"
          >
            <input
              type="text"
              placeholder={
                history?.status === 'escalated'
                  ? 'Conversation ended (Escalated to human)'
                  : history?.status === 'kept'
                  ? 'Payment completed (Promise kept)'
                  : language === 'english'
                  ? 'Type response in English (e.g. I will pay tomorrow morning)...'
                  : 'Type response in Hinglish (e.g. Kal shaam tak de dunga)...'
              }

              className="chat-input"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              disabled={sending || history?.status === 'kept' || history?.status === 'escalated'}
            />
            <button
              type="submit"
              className="btn btn-primary"
              disabled={sending || !inputMessage.trim() || history?.status === 'kept' || history?.status === 'escalated'}
            >
              {sending ? 'Sending...' : 'Send'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
