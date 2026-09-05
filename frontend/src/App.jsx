import React, { useEffect, useState } from 'react';
import { api } from './services/api';
import { Header } from './components/Header';
import { VirtualClockBar } from './components/VirtualClockBar';
import { MetricsBar } from './components/MetricsBar';
import { CaseTable } from './components/CaseTable';
import { AuditDrawer } from './components/AuditDrawer';
import { ChatDrawer } from './components/ChatDrawer';
import { EscalationQueue } from './components/EscalationQueue';
import { WebhookSimulator } from './components/WebhookSimulator';

export function App() {
  const [activeTab, setActiveTab] = useState('pipeline');
  const [clock, setClock] = useState(null);
  const [summary, setSummary] = useState(null);
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedAuditId, setSelectedAuditId] = useState(null);
  const [selectedPromiseId, setSelectedPromiseId] = useState(null);
  const [simEvents, setSimEvents] = useState([]);

  const refreshAll = async () => {
    setLoading(true);
    try {
      const [clockData, summaryData, casesData] = await Promise.all([
        api.getClock(),
        api.getSummary(),
        api.getCases(),
      ]);
      setClock(clockData);
      setSummary(summaryData);
      setCases(casesData);
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshAll();
  }, []);

  const handleRunBatch = async (caseCount = 15) => {
    setLoading(true);
    setSimEvents([]);
    try {
      await api.runBatch(caseCount);
      await refreshAll();
    } catch (err) {
      alert(`Batch run failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleResetBatch = async () => {
    if (!window.confirm('Are you sure you want to reset all simulation data and virtual clock?')) return;
    setLoading(true);
    setSimEvents([]);
    try {
      await api.resetBatch();
      await refreshAll();
    } catch (err) {
      alert(`Reset failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleFastForward = async (days = 1, hours = 0) => {
    setLoading(true);
    try {
      const res = await api.fastForwardClock(days, hours);
      if (res.events_processed && res.events_processed.length > 0) {
        setSimEvents(res.events_processed);
      } else {
        setSimEvents([{ description: `Time advanced by ${days} day(s). No new matured events.` }]);
      }
      await refreshAll();
    } catch (err) {
      alert(`Clock fast-forward failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleResetClock = async () => {
    setLoading(true);
    setSimEvents([]);
    try {
      await api.resetClock();
      await refreshAll();
    } catch (err) {
      alert(`Clock reset failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <Header onRunBatch={handleRunBatch} onResetBatch={handleResetBatch} loading={loading} />

      <main className="main-content">
        <VirtualClockBar
          clock={clock}
          onFastForward={handleFastForward}
          onResetClock={handleResetClock}
          loading={loading}
        />

        {/* Simulation Events Notification Banner */}
        {simEvents.length > 0 && (
          <div className="events-banner">
            <div>
              <strong style={{ display: 'block', marginBottom: '4px' }}>
                Simulation Events Triggered:
              </strong>
              <div className="events-list">
                {simEvents.map((ev, i) => (
                  <div key={i} className="event-item">
                    &bull; {ev.description}
                  </div>
                ))}
              </div>
            </div>
            <button
              className="btn btn-subtle btn-sm"
              onClick={() => setSimEvents([])}
              style={{ color: '#7dd3fc', alignSelf: 'flex-start' }}
            >
              Dismiss
            </button>
          </div>
        )}

        <MetricsBar summary={summary} />

        {/* Navigation Tabs */}
        <div className="toolbar-section">
          <div className="tabs-nav">
            <button
              className={`tab-btn ${activeTab === 'pipeline' ? 'active' : ''}`}
              onClick={() => setActiveTab('pipeline')}
            >
              Recovery Pipeline ({cases.length})
            </button>
            <button
              className={`tab-btn ${activeTab === 'escalations' ? 'active' : ''}`}
              onClick={() => setActiveTab('escalations')}
            >
              Human Escalations ({summary?.status_breakdown?.escalated || 0})
            </button>
            <button
              className={`tab-btn ${activeTab === 'webhooks' ? 'active' : ''}`}
              onClick={() => setActiveTab('webhooks')}
            >
              Razorpay Webhooks
            </button>
          </div>

          <button className="btn btn-subtle btn-sm" onClick={refreshAll} disabled={loading}>
            {loading ? 'Refreshing...' : 'Refresh Data'}
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === 'pipeline' && (
          <CaseTable
            cases={cases}
            onSelectAudit={(id) => setSelectedAuditId(id)}
            onOpenChat={(pId) => setSelectedPromiseId(pId)}
            loading={loading}
          />
        )}

        {activeTab === 'escalations' && <EscalationQueue onRefreshState={refreshAll} />}

        {activeTab === 'webhooks' && <WebhookSimulator onRefreshState={refreshAll} />}
      </main>

      {/* Audit Drawer */}
      {selectedAuditId && (
        <AuditDrawer
          attemptId={selectedAuditId}
          onClose={() => setSelectedAuditId(null)}
          onOpenChat={(pId) => setSelectedPromiseId(pId)}
        />
      )}

      {/* Chat Drawer */}
      {selectedPromiseId && (
        <ChatDrawer
          promiseId={selectedPromiseId}
          onClose={() => setSelectedPromiseId(null)}
          onRefreshState={refreshAll}
        />
      )}
    </div>
  );
}

export default App;
