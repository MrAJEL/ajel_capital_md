import React from 'react';
import { X, Settings } from 'lucide-react';

interface SettingsWindowProps {
  onClose: () => void;
  portfolios: any[];
  activePortfolio: number | null;
  setActivePortfolio: (id: number) => void;
  refreshInterval: number;
  setRefreshInterval: (v: number) => void;
  benchmarkSymbol: string;
  setBenchmarkSymbol: (v: string) => void;
  currency: string;
  setCurrency: (v: string) => void;
  status: any;
  handleCreatePortfolio: (n: string, c?: number) => void;
  clients: any[];
}

export default function SettingsWindow({
  onClose, portfolios, activePortfolio, setActivePortfolio,
  refreshInterval, setRefreshInterval, benchmarkSymbol, setBenchmarkSymbol,
  currency, setCurrency, status, handleCreatePortfolio, clients
}: SettingsWindowProps) {

  const [newPortName, setNewPortName] = React.useState('');
  const [newPortClient, setNewPortClient] = React.useState('');

  return (
    <div style={{
      position: 'fixed', top: 0, right: 0, width: '350px', height: '100vh',
      background: 'var(--bg-secondary)', borderLeft: '1px solid var(--border)',
      boxShadow: '-4px 0 24px rgba(0,0,0,0.5)', zIndex: 1000,
      display: 'flex', flexDirection: 'column',
      animation: 'slideInRight 0.3s ease-out'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1.5rem', borderBottom: '1px solid var(--border)' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Settings size={20} className="text-blue-500" /> Settings
        </h2>
        <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
          <X size={24} />
        </button>
      </div>

      <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem', overflowY: 'auto' }}>
        <div>
          <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '8px', textTransform: 'uppercase' }}>Active Portfolio</label>
          <select 
            value={activePortfolio || ''} 
            onChange={e => setActivePortfolio(Number(e.target.value))}
            style={{ width: '100%', padding: '10px', background: 'var(--bg-input)', border: '1px solid var(--border)', borderRadius: '6px', color: 'var(--text-primary)' }}
          >
            {portfolios.map(p => (
              <option key={p.id} value={p.id}>{p.name} ({p.currency}) {p.client_id ? '👤' : '🏢'}</option>
            ))}
          </select>
        </div>

        {/* Create Portfolio */}
        <div style={{ padding: '1rem', background: 'rgba(255,255,255,0.03)', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)' }}>
          <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-primary)', marginBottom: '12px', fontWeight: 600 }}>Create New Portfolio</label>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <input 
              placeholder="Portfolio Name" value={newPortName} onChange={e => setNewPortName(e.target.value)}
              style={{ width: '100%', padding: '8px', background: 'var(--bg-input)', border: '1px solid var(--border)', borderRadius: '4px', color: 'white', fontSize: '0.85rem' }}
            />
            <select 
              value={newPortClient} onChange={e => setNewPortClient(e.target.value)}
              style={{ width: '100%', padding: '8px', background: 'var(--bg-input)', border: '1px solid var(--border)', borderRadius: '4px', color: 'white', fontSize: '0.85rem' }}
            >
              <option value="">-- Main Pool (No Client) --</option>
              {clients.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
            <button 
              onClick={() => { handleCreatePortfolio(newPortName, newPortClient ? Number(newPortClient) : undefined); setNewPortName(''); setNewPortClient(''); }}
              disabled={!newPortName}
              style={{ padding: '8px', background: 'var(--accent)', color: 'white', border: 'none', borderRadius: '4px', cursor: newPortName ? 'pointer' : 'not-allowed', opacity: newPortName ? 1 : 0.5, fontSize: '0.85rem' }}
            >
              + Create Portfolio
            </button>
          </div>
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '8px', textTransform: 'uppercase' }}>Auto-Refresh (Seconds)</label>
          <div style={{ display: 'flex', gap: '8px' }}>
            {[30, 60, 120, 300].map(sec => (
               <button
                 key={sec}
                 onClick={() => setRefreshInterval(sec)}
                 style={{
                   flex: 1, padding: '8px', borderRadius: '6px', cursor: 'pointer',
                   background: refreshInterval === sec ? 'rgba(59,130,246,0.15)' : 'var(--bg-input)',
                   border: refreshInterval === sec ? '1px solid var(--accent)' : '1px solid var(--border)',
                   color: refreshInterval === sec ? 'var(--accent)' : 'var(--text-secondary)'
                 }}
               >{sec}s</button>
            ))}
          </div>
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '8px', textTransform: 'uppercase' }}>Benchmark Symbol</label>
          <input 
            value={benchmarkSymbol}
            onChange={e => setBenchmarkSymbol(e.target.value)}
            placeholder="SPY"
            style={{ width: '100%', padding: '10px', background: 'var(--bg-input)', border: '1px solid var(--border)', borderRadius: '6px', color: 'var(--text-primary)' }}
          />
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '8px', textTransform: 'uppercase' }}>Base Currency</label>
          <select 
            value={currency} 
            onChange={e => setCurrency(e.target.value)}
            style={{ width: '100%', padding: '10px', background: 'var(--bg-input)', border: '1px solid var(--border)', borderRadius: '6px', color: 'var(--text-primary)' }}
          >
            <option value="USD">USD ($)</option>
            <option value="EUR">EUR (€)</option>
            <option value="GBP">GBP (£)</option>
          </select>
        </div>

        <div style={{ marginTop: 'auto', paddingTop: '1rem', borderTop: '1px solid var(--border)', display: 'flex', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
             <div style={{ width: 8, height: 8, borderRadius: '50%', background: status ? 'var(--success)' : 'var(--danger)' }} /> API
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
             <div style={{ width: 8, height: 8, borderRadius: '50%', background: status?.database === 'connected' ? 'var(--success)' : 'var(--danger)' }} /> Database
          </div>
        </div>
      </div>
    </div>
  );
}
