import React from 'react';
import { Settings, BarChart2, Eye, BookOpen, Users } from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: any) => void;
  status: any;
  statusLoading: boolean;
  setShowSettings: (v: boolean) => void;
}

export default function Sidebar({ activeTab, setActiveTab, status, statusLoading, setShowSettings }: SidebarProps) {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: <BarChart2 size={20} /> },
    { id: 'watchlist', label: 'Watchlist', icon: <Eye size={20} /> },
    { id: 'journal', label: 'Journal', icon: <BookOpen size={20} /> },
    { id: 'clients', label: 'Clients', icon: <Users size={20} /> },
  ];

  return (
    <aside className="sidebar-container">
      <div style={{ padding: '0 1.25rem 1.5rem', display: 'flex', alignItems: 'center', gap: '10px' }}>
        <svg width="32" height="32" viewBox="0 0 28 28" fill="none">
          <rect x="2" y="2" width="24" height="24" rx="6" stroke="#3B82F6" strokeWidth="2" fill="none" />
          <path d="M8 18L14 8L20 18" stroke="#3B82F6" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
          <line x1="10" y1="15" x2="18" y2="15" stroke="#3B82F6" strokeWidth="2" strokeLinecap="round" />
        </svg>
        <span style={{ fontSize: '0.95rem', fontWeight: 700, letterSpacing: '0.08em', color: 'var(--accent)' }}>AJEL CAPITAL</span>
      </div>

      <nav className="sidebar-nav" style={{ flex: 1 }}>
        {navItems.map(item => (
          <button
            key={item.id}
            className={activeTab === item.id ? "active-tab" : ""}
            onClick={() => setActiveTab(item.id)}
            style={{
              display: 'flex', alignItems: 'center', gap: '12px', width: '100%',
              padding: '12px 1.25rem', border: 'none', cursor: 'pointer',
              background: activeTab === item.id ? 'rgba(59,130,246,0.1)' : 'transparent',
              color: activeTab === item.id ? 'var(--accent)' : 'var(--text-secondary)',
              borderLeft: activeTab === item.id ? '3px solid var(--accent)' : '3px solid transparent',
              fontSize: '0.9rem', fontWeight: activeTab === item.id ? 600 : 400,
              transition: 'var(--transition)', fontFamily: 'inherit',
            }}
          >
            {item.icon}
            {item.label}
          </button>
        ))}
      </nav>

      <div style={{ padding: '0 1.25rem', marginBottom: '1rem' }}>
        <button
          onClick={() => setShowSettings(true)}
          style={{
            display: 'flex', alignItems: 'center', gap: '8px', width: '100%',
            padding: '10px 14px', background: 'var(--bg-input)', border: '1px solid var(--border)',
            borderRadius: 'var(--radius)', color: 'var(--text-secondary)', cursor: 'pointer',
            fontSize: '0.85rem', fontWeight: 500, transition: 'var(--transition)'
          }}
        >
          <Settings size={16} /> Configuración
        </button>
      </div>

      <div style={{ padding: '1rem 1.25rem', borderTop: '1px solid var(--border)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          <div style={{
            width: '6px', height: '6px', borderRadius: '50%',
            background: status ? 'var(--success)' : statusLoading ? 'var(--warning)' : 'var(--danger)',
            boxShadow: `0 0 6px ${status ? 'var(--success)' : 'var(--danger)'}`,
          }} />
          {statusLoading ? 'Connecting...' : status ? `API v${status.version}` : 'Offline'}
        </div>
      </div>
    </aside>
  );
}
