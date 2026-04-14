import React, { useState } from 'react';
import { User, Briefcase, Trash2, ArrowRight, Download, Activity, DollarSign, TrendingUp } from 'lucide-react';
import * as api from '../lib/api';

export default function ClientManagement({ 
  clients, handleCreateClient, handleDeleteClient, isCreatingClient, onRefreshClients, portfolios
}: any) {

  const [newClient, setNewClient] = useState({ 
    name: '', email: '', risk_profile: 'moderate', aum: 0, 
    initial_capital: 0, management_fee_pct: 2.0, performance_fee_pct: 20.0, entry_date: '',
    portfolio_type: 'pool' as 'pool' | 'personal'
  });
  const [selectedClient, setSelectedClient] = useState<any>(null);
  const [feeEvents, setFeeEvents] = useState<any[]>([]);
  const [showChargeFee, setShowChargeFee] = useState(false);
  const [chargeFeeType, setChargeFeeType] = useState('management_monthly');
  const [chargeFeeAmount, setChargeFeeAmount] = useState(0);
  const [addCapitalAmount, setAddCapitalAmount] = useState(0);
  const [showAddCapital, setShowAddCapital] = useState(false);
  const [addCapitalPortfolioId, setAddCapitalPortfolioId] = useState('');

  const performCreate = async () => {
    const clientData = { 
      ...newClient,
      initial_capital: newClient.initial_capital || newClient.aum,
    };
    
    await handleCreateClient(clientData);
    
    // Always create an individual portfolio for this client
    try {
      const res = await api.getClients();
      // Since names might not be perfectly unique if fast, it's a fallback. Best is if backend returns ID.
      // But we will fetch via a timeout or use latest.
      const created = (res.clients || []).find((c: any) => c.name === newClient.name);
      if (created) {
        await api.createPortfolio({
          name: `${newClient.name} Portfolio`,
          client_id: created.id,
          currency: 'USD',
        });
      }
    } catch (e) { console.error('Error creating individual portfolio:', e); }
    
    if (onRefreshClients) onRefreshClients();
    setNewClient({ name: '', email: '', risk_profile: 'moderate', aum: 0, initial_capital: 0, management_fee_pct: 2.0, performance_fee_pct: 20.0, entry_date: '', portfolio_type: 'personal' });
  };

  const openProfile = async (client: any) => {
    setSelectedClient(client);
    try {
      const res = await api.getClient(client.id);
      setSelectedClient(res);
      // Load fee events
      const feRes = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/clients/${client.id}/fee-events`);
      if (feRes.ok) {
        const feData = await feRes.json();
        setFeeEvents(feData.fee_events || []);
      }
    } catch(e) { console.error(e); }
  };

  const handleChargeFee = async () => {
    if (!selectedClient || chargeFeeAmount <= 0) return;
    try {
      const base = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
      await fetch(`${base}/clients/${selectedClient.id}/charge-fee`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event_type: chargeFeeType, amount: chargeFeeAmount, notes: `Charged via dashboard` }),
      });
      setShowChargeFee(false);
      openProfile(selectedClient); // Refresh
      if (onRefreshClients) onRefreshClients();
    } catch(e) { console.error(e); }
  };

  const handleAddCapital = async () => {
    if (!selectedClient || addCapitalAmount <= 0) return;
    try {
      const base = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
      let url = `${base}/clients/${selectedClient.id}/add-capital?amount=${addCapitalAmount}`;
      if (addCapitalPortfolioId) url += `&portfolio_id=${addCapitalPortfolioId}`;
      await fetch(url, { method: 'POST' });
      setShowAddCapital(false);
      setAddCapitalAmount(0);
      setAddCapitalPortfolioId('');
      openProfile(selectedClient);
      if (onRefreshClients) onRefreshClients();
    } catch(e) { console.error(e); }
  };

  const exportReport = () => {
    if (!selectedClient) return;
    const c = selectedClient;
    const aum = c.aum || 0;
    const hwm = c.hwm || aum;
    const mgmt = c.management_fee_pct || 2;
    const perf = c.performance_fee_pct || 20;
    const monthlyFee = aum * (mgmt / 100) / 12;
    const annualFee = aum * (mgmt / 100);
    const perfFee = Math.max(0, aum - hwm) * (perf / 100);

    const report = `AJEL CAPITAL — Client Report
============================
Name:            ${c.name}
Email:           ${c.email || 'N/A'}
Risk Profile:    ${c.risk_profile}
Entry Date:      ${c.entry_date ? new Date(c.entry_date).toLocaleDateString() : 'N/A'}

CAPITAL
  Initial Capital: $${(c.initial_capital || 0).toLocaleString()}
  Current AUM:     $${aum.toLocaleString()}
  High Water Mark: $${hwm.toLocaleString()}
  ${c.hwm_updated_at ? `HWM Updated: ${new Date(c.hwm_updated_at).toLocaleDateString()}` : ''}

FEE STRUCTURE
  Management Fee:  ${mgmt}% annual
  Performance Fee: ${perf}% over HWM

CURRENT CALCULATIONS
  Monthly Fee Est: $${monthlyFee.toFixed(2)}
  Annual Fee Est:  $${annualFee.toFixed(2)}
  Perf Fee Pend:   $${perfFee.toFixed(2)}
  Total Charged:   $${(c.total_fees_charged || 0).toFixed(2)}

FEE HISTORY
${feeEvents.map((e: any) => `  ${new Date(e.created_at).toLocaleDateString()} | ${e.event_type} | $${e.amount.toFixed(2)}`).join('\n') || '  No fees charged yet.'}

Generated: ${new Date().toISOString()}
`;
    const blob = new Blob([report], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = `${c.name.replace(/\s+/g, '_')}_report.txt`; a.click();
    URL.revokeObjectURL(url);
  };

  // Fee calculations for selected client
  const calcFees = (c: any) => {
    const aum = c?.aum || 0;
    const hwm = c?.hwm || aum;
    const mgmt = c?.management_fee_pct || 2;
    const perf = c?.performance_fee_pct || 20;
    return {
      monthlyMgmt: aum * (mgmt / 100) / 12,
      annualMgmt: aum * (mgmt / 100),
      gainsOverHwm: Math.max(0, aum - hwm),
      performanceFee: Math.max(0, aum - hwm) * (perf / 100),
    };
  };

  // Suggested fee amount based on type
  const getSuggestedFee = () => {
    if (!selectedClient) return 0;
    const f = calcFees(selectedClient);
    if (chargeFeeType === 'management_monthly') return f.monthlyMgmt;
    if (chargeFeeType === 'management_annual') return f.annualMgmt;
    if (chargeFeeType === 'performance_5yr') return f.performanceFee;
    return 0;
  };

  React.useEffect(() => {
    setChargeFeeAmount(getSuggestedFee());
  }, [chargeFeeType, selectedClient]);

  const ClientProfileModal = () => {
    if (!selectedClient) return null;
    const fees = calcFees(selectedClient);
    
    return (
      <div style={{ position: 'fixed', top: 0, left: 0, width: '100%', height: '100%', background: 'rgba(0,0,0,0.7)', zIndex: 2000, display: 'flex', justifyContent: 'flex-end' }}>
        <div style={{ background: 'var(--bg-secondary)', width: '500px', height: '100%', borderLeft: '1px solid var(--border)', display: 'flex', flexDirection: 'column', animation: 'slideInRight 0.3s ease-out' }}>
           <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
             <h2 style={{ fontSize: '1.25rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '10px' }}>
               <User size={20} style={{ color: 'var(--accent)' }} /> {selectedClient.name}
             </h2>
             <button onClick={() => { setSelectedClient(null); setShowChargeFee(false); setShowAddCapital(false); }} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '1.5rem' }}>&times;</button>
           </div>
           
           <div style={{ padding: '1.5rem', flex: 1, overflowY: 'auto' }}>
             {/* AUM */}
             <div style={{ background: 'var(--bg-input)', padding: '1rem', borderRadius: '8px', marginBottom: '1.5rem' }}>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '4px' }}>Current AUM</div>
                <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--accent)' }}>${(selectedClient.aum || 0).toLocaleString()}</div>
                {selectedClient.initial_capital > 0 && <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>Initial: ${selectedClient.initial_capital.toLocaleString()}</div>}
             </div>

             {/* KPI Grid */}
             <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
               <div style={{ padding: '0.75rem', background: 'var(--bg-input)', borderRadius: '8px' }}>
                 <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>High Water Mark</div>
                 <div style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-primary)' }}>${(selectedClient.hwm || 0).toLocaleString()}</div>
                 {selectedClient.hwm_updated_at && <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>{new Date(selectedClient.hwm_updated_at).toLocaleDateString()}</div>}
               </div>
               <div style={{ padding: '0.75rem', background: 'var(--bg-input)', borderRadius: '8px' }}>
                 <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Gains Over HWM</div>
                 <div style={{ fontSize: '1.1rem', fontWeight: 600, color: fees.gainsOverHwm > 0 ? 'var(--success)' : 'var(--text-secondary)' }}>${fees.gainsOverHwm.toLocaleString()}</div>
               </div>
             </div>

             {/* Fee Calculations */}
             <div style={{ marginBottom: '1.5rem' }}>
                <h3 style={{ fontSize: '0.9rem', color: 'var(--text-primary)', marginBottom: '1rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem' }}>Fee Structure</h3>
                <div style={{ background: 'rgba(59,130,246,0.05)', border: '1px solid rgba(59,130,246,0.2)', padding: '1rem', borderRadius: '8px', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                   <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Monthly Mgmt ({selectedClient.management_fee_pct || 2}%/yr ÷ 12)</span>
                      <span style={{ fontWeight: 600, color: 'var(--accent)' }}>+${fees.monthlyMgmt.toFixed(2)}</span>
                   </div>
                   <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Annual Mgmt ({selectedClient.management_fee_pct || 2}%)</span>
                      <span style={{ fontWeight: 600, color: 'var(--accent)' }}>+${fees.annualMgmt.toFixed(2)}</span>
                   </div>
                   <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Performance ({selectedClient.performance_fee_pct || 20}% &gt; HWM, each 5yr)</span>
                      <span style={{ fontWeight: 600, color: fees.performanceFee > 0 ? 'var(--gold)' : 'var(--text-muted)' }}>+${fees.performanceFee.toFixed(2)}</span>
                   </div>
                   <div style={{ borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '0.75rem', display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>Total Charged to Date</span>
                      <span style={{ fontWeight: 700, fontSize: '1.1rem', color: 'var(--success)' }}>${(selectedClient.total_fees_charged || 0).toFixed(2)}</span>
                   </div>
                </div>
             </div>

             {/* Action Buttons */}
             <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.5rem' }}>
               <button onClick={() => { setShowChargeFee(true); setShowAddCapital(false); }} style={{ flex: 1, padding: '10px', background: 'linear-gradient(135deg, #8B5CF6, #6D28D9)', border: 'none', borderRadius: '6px', color: 'white', fontWeight: 600, cursor: 'pointer', fontSize: '0.85rem' }}>
                 <DollarSign size={14} style={{ display: 'inline', verticalAlign: 'middle' }} /> Charge Fee
               </button>
               <button onClick={() => { setShowAddCapital(true); setShowChargeFee(false); }} style={{ flex: 1, padding: '10px', background: 'linear-gradient(135deg, #10B981, #059669)', border: 'none', borderRadius: '6px', color: 'white', fontWeight: 600, cursor: 'pointer', fontSize: '0.85rem' }}>
                 <TrendingUp size={14} style={{ display: 'inline', verticalAlign: 'middle' }} /> Add Capital
               </button>
             </div>

             {/* Charge Fee Panel */}
             {showChargeFee && (
               <div style={{ padding: '1rem', background: 'var(--bg-card)', border: '1px solid rgba(139,92,246,0.3)', borderRadius: '8px', marginBottom: '1.5rem' }}>
                 <h4 style={{ fontSize: '0.85rem', marginBottom: '0.75rem', color: 'var(--text-primary)' }}>Charge Fee</h4>
                 <div style={{ marginBottom: '0.75rem' }}>
                   <select value={chargeFeeType} onChange={e => setChargeFeeType(e.target.value)} style={{ width: '100%', padding: '8px', background: 'var(--bg-input)', border: '1px solid var(--border)', borderRadius: '6px', color: 'white', fontSize: '0.85rem' }}>
                     <option value="management_monthly">Management Monthly</option>
                     <option value="management_annual">Management Annual</option>
                     <option value="performance_5yr">Performance (5yr)</option>
                   </select>
                 </div>
                 {chargeFeeType === 'performance_5yr' && fees.performanceFee === 0 && (
                   <div style={{ padding: '0.5rem', background: 'rgba(245,158,11,0.1)', borderRadius: '4px', fontSize: '0.75rem', color: '#F59E0B', marginBottom: '0.75rem' }}>
                     ⚠ No gains over HWM — performance fee is $0
                   </div>
                 )}
                 {chargeFeeType === 'performance_5yr' && fees.performanceFee > 0 && (
                   <div style={{ padding: '0.5rem', background: 'rgba(59,130,246,0.1)', borderRadius: '4px', fontSize: '0.75rem', color: '#3B82F6', marginBottom: '0.75rem' }}>
                     ℹ HWM will update to current AUM after charging
                   </div>
                 )}
                 <div style={{ display: 'flex', gap: '0.5rem' }}>
                   <input type="number" value={chargeFeeAmount} onChange={e => setChargeFeeAmount(Number(e.target.value))} style={{ flex: 1, padding: '8px', background: 'var(--bg-input)', border: '1px solid var(--border)', borderRadius: '6px', color: 'white' }} />
                   <button onClick={handleChargeFee} disabled={chargeFeeAmount <= 0} style={{ padding: '8px 16px', background: chargeFeeAmount > 0 ? '#8B5CF6' : 'var(--bg-input)', border: 'none', borderRadius: '6px', color: 'white', fontWeight: 600, cursor: chargeFeeAmount > 0 ? 'pointer' : 'default', opacity: chargeFeeAmount > 0 ? 1 : 0.5 }}>Charge</button>
                 </div>
               </div>
             )}

             {/* Add Capital Panel */}
            {showAddCapital && (
               <div style={{ padding: '1rem', background: 'var(--bg-card)', border: '1px solid rgba(16,185,129,0.3)', borderRadius: '8px', marginBottom: '1.5rem' }}>
                 <h4 style={{ fontSize: '0.85rem', marginBottom: '0.75rem', color: 'var(--text-primary)' }}>Add Capital</h4>
                 <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>Deposit automatically logs to the selected portfolio and tracks entry HWM.</div>
                 
                 <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                   <select 
                     value={addCapitalPortfolioId} onChange={e => setAddCapitalPortfolioId(e.target.value)}
                     style={{ width: '100%', padding: '8px', background: 'var(--bg-input)', border: '1px solid var(--border)', borderRadius: '6px', color: 'white' }}
                   >
                     <option value="">— Select Target Portfolio —</option>
                     {(portfolios || []).map((p: any) => (
                       <option key={p.id} value={p.id}>{p.client_name ? `${p.name} — ${p.client_name}` : `${p.name} (Pool)`}</option>
                     ))}
                   </select>

                   <div style={{ display: 'flex', gap: '0.5rem' }}>
                     <input type="number" placeholder="Amount ($)" value={addCapitalAmount || ''} onChange={e => setAddCapitalAmount(Number(e.target.value))} style={{ flex: 1, padding: '8px', background: 'var(--bg-input)', border: '1px solid var(--border)', borderRadius: '6px', color: 'white' }} />
                     <button onClick={handleAddCapital} disabled={addCapitalAmount <= 0} style={{ padding: '8px 16px', background: addCapitalAmount > 0 ? '#10B981' : 'var(--bg-input)', border: 'none', borderRadius: '6px', color: 'white', fontWeight: 600, cursor: addCapitalAmount > 0 ? 'pointer' : 'default' }}>Add</button>
                   </div>
                 </div>
               </div>
             )}

             {/* Fee History */}
             <div style={{ marginBottom: '1.5rem' }}>
               <h3 style={{ fontSize: '0.9rem', color: 'var(--text-primary)', marginBottom: '1rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem' }}>Fee History</h3>
               {feeEvents.length === 0 ? (
                 <div style={{ padding: '1rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>No fees charged yet.</div>
               ) : (
                 <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                   {feeEvents.map((fe: any) => (
                     <div key={fe.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 12px', background: 'var(--bg-input)', borderRadius: '6px', fontSize: '0.8rem' }}>
                       <div>
                         <span style={{ color: 'var(--text-secondary)', textTransform: 'capitalize' }}>{fe.event_type.replace(/_/g, ' ')}</span>
                         <span style={{ color: 'var(--text-muted)', marginLeft: '10px' }}>{new Date(fe.created_at).toLocaleDateString()}</span>
                       </div>
                       <span style={{ fontWeight: 600, color: 'var(--accent)' }}>${fe.amount.toFixed(2)}</span>
                     </div>
                   ))}
                 </div>
               )}
             </div>

             {/* Export */}
             <button onClick={exportReport} style={{ width: '100%', padding: '10px', background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '6px', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', cursor: 'pointer' }}>
               <Download size={16} /> Export Report (.txt)
             </button>
           </div>
        </div>
      </div>
    );
  };

  return (
    <div className="animate-fadeIn">
      <ClientProfileModal />

      <h1 style={{ fontSize: '1.75rem', fontWeight: 700, marginBottom: '0.5rem' }}>Client Directory</h1>
      <p style={{ color: 'var(--text-muted)', marginBottom: '2rem', fontSize: '0.9rem' }}>Manage advisory clients, fee structures, and portfolio assignments</p>

      <div className="grid-cols-layout">
        
        {/* Create Client Form */}
        <div style={{ padding: '1.5rem', borderRadius: 'var(--radius)', background: 'var(--bg-card)', border: '1px solid var(--border)', alignSelf: 'start' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1.5rem', color: 'var(--text-primary)' }}>Onboard Client</h3>
          
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>NAME</label>
            <input placeholder="e.g. John Doe LLC" value={newClient.name} onChange={e => setNewClient({...newClient, name: e.target.value})} style={{ width: '100%', padding: '10px', background: 'var(--bg-input)', border: '1px solid var(--border)', borderRadius: '6px', color: 'white' }} />
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>EMAIL</label>
            <input type="email" placeholder="john@example.com" value={newClient.email} onChange={e => setNewClient({...newClient, email: e.target.value})} style={{ width: '100%', padding: '10px', background: 'var(--bg-input)', border: '1px solid var(--border)', borderRadius: '6px', color: 'white' }} />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
             <div>
               <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>RISK PROFILE</label>
               <select value={newClient.risk_profile} onChange={e => setNewClient({...newClient, risk_profile: e.target.value})} style={{ width: '100%', padding: '10px', background: 'var(--bg-input)', border: '1px solid var(--border)', borderRadius: '6px', color: 'white' }}>
                 <option value="conservative">Conservative</option>
                 <option value="moderate">Moderate</option>
                 <option value="aggressive">Aggressive</option>
               </select>
             </div>
             <div>
               <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>INITIAL CAPITAL ($)</label>
               <input type="number" step="any" placeholder="10000" value={newClient.initial_capital || ''} onChange={e => setNewClient({...newClient, initial_capital: Number(e.target.value), aum: Number(e.target.value)})} style={{ width: '100%', padding: '10px', background: 'var(--bg-input)', border: '1px solid var(--border)', borderRadius: '6px', color: 'white' }} />
             </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
             <div>
               <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>MGMT FEE (%/yr)</label>
               <input type="number" step="0.1" value={newClient.management_fee_pct} onChange={e => setNewClient({...newClient, management_fee_pct: Number(e.target.value)})} style={{ width: '100%', padding: '10px', background: 'var(--bg-input)', border: '1px solid var(--border)', borderRadius: '6px', color: 'white' }} />
             </div>
             <div>
               <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>PERF FEE (%)</label>
               <input type="number" step="0.1" value={newClient.performance_fee_pct} onChange={e => setNewClient({...newClient, performance_fee_pct: Number(e.target.value)})} style={{ width: '100%', padding: '10px', background: 'var(--bg-input)', border: '1px solid var(--border)', borderRadius: '6px', color: 'white' }} />
             </div>
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>ENTRY DATE</label>
            <input type="date" value={newClient.entry_date} onChange={e => setNewClient({...newClient, entry_date: e.target.value})} style={{ width: '100%', padding: '10px', background: 'var(--bg-input)', border: '1px solid var(--border)', borderRadius: '6px', color: 'white' }} />
          </div>

          <div style={{ marginBottom: '1.5rem', padding: '10px', background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.3)', borderRadius: '8px', color: '#10B981', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
             ℹ Un portafolio individual será creado automáticamente para este cliente.
          </div>

          <button onClick={performCreate} disabled={isCreatingClient || !newClient.name} style={{ width: '100%', padding: '12px', background: 'var(--accent)', color: 'white', border: 'none', borderRadius: '6px', fontWeight: 600, fontSize: '0.9rem', cursor: 'pointer', opacity: (!newClient.name) ? 0.5 : 1 }}>
            {isCreatingClient ? 'Creating...' : '+ Add Client'}
          </button>
        </div>

        {/* Client Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '1rem', alignContent: 'start' }}>
           {clients.length === 0 ? (
             <div style={{ gridColumn: '1 / -1', padding: '3rem', textAlign: 'center', color: 'var(--text-muted)', background: 'var(--bg-card)', borderRadius: 'var(--radius)', border: '1px solid var(--border)' }}>
                No clients yet. Add your first client to start tracking fees.
             </div>
           ) : clients.map((c: any) => (
             <div key={c.id} onClick={() => openProfile(c)} style={{
               padding: '1.25rem', borderRadius: 'var(--radius)', background: 'var(--bg-card)',
               border: '1px solid var(--border)', display: 'flex', flexDirection: 'column',
               cursor: 'pointer', transition: 'var(--transition)', position: 'relative'
             }}>
                <button onClick={(e) => { e.stopPropagation(); handleDeleteClient(c.id); }} style={{ position: 'absolute', top: '10px', right: '10px', background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
                  <Trash2 size={16} />
                </button>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '1rem' }}>
                  <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: 'rgba(59,130,246,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--accent)' }}>
                    <User size={20} />
                  </div>
                  <div>
                    <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '1.05rem' }}>{c.name}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'capitalize' }}>{c.risk_profile} Risk</div>
                  </div>
                </div>
                
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>AUM:</span>
                  <span style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)' }}>${(c.aum || 0).toLocaleString()}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Mgmt Fee:</span>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-primary)' }}>{c.management_fee_pct || 2}% / yr</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Perf Fee:</span>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-primary)' }}>{c.performance_fee_pct || 20}% &gt; HWM</span>
                </div>

                <div style={{ display: 'flex', gap: '8px', marginBottom: '1rem' }}>
                  <button onClick={(e) => { e.stopPropagation(); openProfile(c); setTimeout(() => setShowAddCapital(true), 100); }} style={{ flex: 1, padding: '6px', background: 'rgba(16,185,129,0.1)', color: '#10B981', border: '1px solid rgba(16,185,129,0.3)', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 600, cursor: 'pointer' }}>
                    + Capital
                  </button>
                  <button onClick={(e) => { e.stopPropagation(); openProfile(c); setTimeout(() => setShowChargeFee(true), 100); }} style={{ flex: 1, padding: '6px', background: 'rgba(139,92,246,0.1)', color: '#8B5CF6', border: '1px solid rgba(139,92,246,0.3)', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 600, cursor: 'pointer' }}>
                    $ Charge
                  </button>
                </div>

                <div style={{ marginTop: 'auto', paddingTop: '0.75rem', borderTop: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: 'var(--accent)', fontSize: '0.85rem' }}>
                  <span>View Full Profile</span>
                  <ArrowRight size={16} />
                </div>
             </div>
           ))}
        </div>
      </div>
    </div>
  );
}
