import React, { useState } from 'react';
import { Target, Trash2, Plus, ArrowUpRight, ArrowDownRight, UploadCloud } from 'lucide-react';

export default function ManagementView({ 
  transactions, handleTxnChange, activeTxnForm, 
  handleCreateTransaction, handleDeleteTransaction, isSubmittingTxn,
  portfolios, clients, activePortfolio, setActivePortfolio
}: any) {

  // Build portfolio options: Main Pool + client portfolios
  const portfolioOptions = (portfolios || []).map((p: any) => ({
    id: p.id,
    label: p.client_name ? `${p.name} — ${p.client_name}` : `${p.name} (Pool)`,
  }));

  // Determine if symbol/qty/price fields should show
  const txType = (activeTxnForm.type || 'BUY').toUpperCase();
  const showSymbolFields = !['DEPOSIT', 'WITHDRAWAL', 'FEE'].includes(txType);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    // Deprecated CSV Import
  };

  return (
    <div className="animate-fadeIn">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2rem' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700, marginBottom: '0.5rem' }}>Portfolio & Journal</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Record transactions, choose target portfolio, and log trading emotions</p>
        </div>
        <div>
          {/* Import CSV removed */}
        </div>
      </div>

      <div className="grid-cols-layout">
        
        {/* Transaction Form */}
        <div style={{ padding: '1.5rem', borderRadius: 'var(--radius)', background: 'var(--bg-card)', border: '1px solid var(--border)', alignSelf: 'start' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1.5rem', color: 'var(--text-primary)' }}>New Transaction</h3>
          
          {/* Portfolio Selector */}
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>TARGET PORTFOLIO</label>
            <select 
              value={activeTxnForm.portfolio_id || activePortfolio || ''} 
              onChange={e => {
                const val = Number(e.target.value);
                handleTxnChange('portfolio_id', val);
                if (setActivePortfolio) setActivePortfolio(val);
              }}
              style={{ width: '100%', padding: '10px', background: 'var(--bg-input)', border: '1px solid var(--border)', borderRadius: '6px', color: 'white' }}
            >
              <option value="">— Select Portfolio —</option>
              {portfolioOptions.map((p: any) => (
                <option key={p.id} value={p.id}>{p.label}</option>
              ))}
            </select>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
             <div>
               <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>TYPE</label>
               <select 
                 value={activeTxnForm.type || 'BUY'} onChange={e => handleTxnChange('type', e.target.value)}
                 style={{ width: '100%', padding: '10px', background: 'var(--bg-input)', border: '1px solid var(--border)', borderRadius: '6px', color: 'white' }}
               >
                 <option value="BUY">BUY</option>
                 <option value="SELL">SELL</option>
                 <option value="DIVIDEND">DIVIDEND</option>
                 <option value="DEPOSIT">DEPOSIT</option>
                 <option value="WITHDRAWAL">WITHDRAWAL</option>
                 <option value="STOCK_SPLIT">STOCK SPLIT</option>
                 <option value="FEE">FEE</option>
               </select>
             </div>
             <div>
               <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>ASSET CLASS</label>
               <select 
                 value={activeTxnForm.asset_type || 'stock'} onChange={e => handleTxnChange('asset_type', e.target.value)}
                 disabled={!showSymbolFields}
                 style={{ width: '100%', padding: '10px', background: 'var(--bg-input)', border: '1px solid var(--border)', borderRadius: '6px', color: 'white', opacity: showSymbolFields ? 1 : 0.5 }}
               >
                 <option value="stock">Stock</option>
                 <option value="etf">ETF</option>
                 <option value="crypto">Crypto</option>
                 <option value="bond">Bond</option>
                 <option value="commodity">Commodity</option>
                 <option value="cash">Cash</option>
               </select>
             </div>
          </div>

          {showSymbolFields && (
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>SYMBOL</label>
              <input 
                placeholder="e.g. AAPL, BTC-USD" value={activeTxnForm.symbol || ''} onChange={e => handleTxnChange('symbol', e.target.value.toUpperCase())}
                style={{ width: '100%', padding: '10px', background: 'var(--bg-input)', border: '1px solid var(--border)', borderRadius: '6px', color: 'white', letterSpacing: '0.05em' }}
              />
            </div>
          )}

          {showSymbolFields && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
               <div>
                 <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>QTY</label>
                 <input 
                   type="number" step="any" placeholder="0" value={activeTxnForm.qty || ''} onChange={e => handleTxnChange('qty', e.target.value)}
                   style={{ width: '100%', padding: '10px', background: 'var(--bg-input)', border: '1px solid var(--border)', borderRadius: '6px', color: 'white' }}
                 />
               </div>
               <div>
                 <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>PRICE ($)</label>
                 <input 
                   type="number" step="any" placeholder="0" value={activeTxnForm.price || ''} onChange={e => handleTxnChange('price', e.target.value)}
                   style={{ width: '100%', padding: '10px', background: 'var(--bg-input)', border: '1px solid var(--border)', borderRadius: '6px', color: 'white' }}
                 />
               </div>
            </div>
          )}

          {/* Total Amount — auto-computed or manual for deposits */}
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>
              TOTAL AMOUNT ($) {showSymbolFields && '(auto)'}
            </label>
            <input 
              type="number" step="any" placeholder="0" 
              value={
                showSymbolFields 
                  ? ((parseFloat(activeTxnForm.qty || '0') * parseFloat(activeTxnForm.price || '0')) || '') 
                  : (activeTxnForm.total_amount || '')
              } 
              onChange={e => handleTxnChange('total_amount', e.target.value)}
              readOnly={showSymbolFields}
              style={{ width: '100%', padding: '10px', background: showSymbolFields ? 'rgba(59,130,246,0.05)' : 'var(--bg-input)', border: '1px solid var(--border)', borderRadius: '6px', color: 'white' }}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
             <div>
               <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>FEES ($)</label>
               <input 
                 type="number" step="any" placeholder="0" value={activeTxnForm.fees || ''} onChange={e => handleTxnChange('fees', e.target.value)}
                 style={{ width: '100%', padding: '10px', background: 'var(--bg-input)', border: '1px solid var(--border)', borderRadius: '6px', color: 'white' }}
               />
             </div>
             <div>
               <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>DATE</label>
               <input 
                 type="date" value={activeTxnForm.date ? activeTxnForm.date.substring(0, 10) : ''} onChange={e => handleTxnChange('date', e.target.value)}
                 style={{ width: '100%', padding: '10px', background: 'var(--bg-input)', border: '1px solid var(--border)', borderRadius: '6px', color: 'white' }}
               />
             </div>
          </div>

          {/* Broker */}
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>BROKER / PLATFORM</label>
            <input 
              placeholder="e.g. Interactive Brokers, Coinbase" value={activeTxnForm.broker || ''} onChange={e => handleTxnChange('broker', e.target.value)}
              style={{ width: '100%', padding: '10px', background: 'var(--bg-input)', border: '1px solid var(--border)', borderRadius: '6px', color: 'white' }}
            />
          </div>

          <hr style={{ border: 'none', borderTop: '1px solid var(--border)', margin: '1.5rem 0' }} />
          <h4 style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: '1rem', textTransform: 'uppercase' }}>Journal Details</h4>

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>EMOTION</label>
            <select 
              value={activeTxnForm.emotion || ''} onChange={e => handleTxnChange('emotion', e.target.value)}
              style={{ width: '100%', padding: '10px', background: 'var(--bg-input)', border: '1px solid var(--border)', borderRadius: '6px', color: 'white' }}
            >
              <option value="">(None)</option>
              <option value="conviccion">Convicción</option>
              <option value="dca">DCA</option>
              <option value="fomo">FOMO</option>
              <option value="gestion_riesgo">Gestión de Riesgo</option>
              <option value="panico">Pánico</option>
              <option value="codicia">Codicia</option>
              <option value="miedo">Miedo</option>
              <option value="neutral">Neutral</option>
            </select>
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>THESIS / NOTES</label>
            <textarea 
              placeholder="Why are you making this trade? (for AI training)" value={activeTxnForm.thesis || ''} onChange={e => handleTxnChange('thesis', e.target.value)}
              style={{ width: '100%', padding: '10px', background: 'var(--bg-input)', border: '1px solid var(--border)', borderRadius: '6px', color: 'white', minHeight: '80px', resize: 'vertical' }}
            />
          </div>

          <button 
            onClick={handleCreateTransaction} disabled={isSubmittingTxn}
            style={{ 
              width: '100%', padding: '12px', background: 'var(--accent)', color: 'white', border: 'none', 
              borderRadius: '6px', fontWeight: 600, fontSize: '0.9rem', cursor: 'pointer', transition: 'filter 0.2s' 
            }}
          >
            {isSubmittingTxn ? 'Submitting...' : '💾 Save Transaction'}
          </button>
        </div>

        {/* Transaction History & Journal List */}
        <div style={{ padding: '1.5rem', borderRadius: 'var(--radius)', background: 'var(--bg-card)', border: '1px solid var(--border)', display: 'flex', flexDirection: 'column' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1.5rem', color: 'var(--text-primary)' }}>History & Journal Logs</h3>
          
          {transactions.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--text-muted)' }}>
              No transactions found. Select a portfolio and add your first transaction.
            </div>
          ) : (
            <div style={{ overflowY: 'auto', flex: 1, paddingRight: '10px' }}>
              {transactions.map((t: any) => {
                const total = t.total_amount || ((t.qty || 0) * (t.price || 0));
                return (
                 <div key={t.id} style={{ 
                   display: 'grid', gridTemplateColumns: '1fr', gap: '10px', padding: '1rem', 
                   background: 'var(--bg-input)', borderRadius: '8px', marginBottom: '1rem', border: '1px solid var(--border)' 
                 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                       <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                         <span style={{ 
                           padding: '4px 8px', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 700,
                           background: t.type === 'BUY' ? 'rgba(16,185,129,0.1)' : t.type === 'SELL' ? 'rgba(239,68,68,0.1)' : t.type === 'DEPOSIT' ? 'rgba(59,130,246,0.1)' : 'rgba(160,174,192,0.1)',
                           color: t.type === 'BUY' ? 'var(--success)' : t.type === 'SELL' ? 'var(--danger)' : t.type === 'DEPOSIT' ? 'var(--accent)' : 'var(--text-secondary)'
                         }}>
                            {t.type} {t.qty ? `${t.qty}` : ''} {t.symbol || ''}
                         </span>
                         {t.price > 0 && <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>@ ${t.price}</span>}
                         <span style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)' }}>${total.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
                       </div>
                       <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                         <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{t.date ? new Date(t.date).toLocaleDateString() : ''}</span>
                         <button onClick={() => handleDeleteTransaction(t.id)} style={{ background: 'none', border: 'none', color: 'var(--danger)', cursor: 'pointer', padding: '2px' }}><Trash2 size={16}/></button>
                       </div>
                    </div>
                    
                    {(t.emotion || t.thesis || t.broker) && (
                      <div style={{ marginTop: '0.5rem', paddingTop: '0.5rem', borderTop: '1px dashed rgba(255,255,255,0.1)', fontSize: '0.85rem' }}>
                         {t.broker && <div style={{ marginBottom: '4px' }}><span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>BROKER:</span> <span style={{ color: 'var(--text-secondary)' }}>{t.broker}</span></div>}
                         {t.emotion && <div style={{ marginBottom: '4px' }}><span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>EMOTION:</span> <span style={{ color: 'var(--gold)', textTransform: 'capitalize' }}>{t.emotion}</span></div>}
                         {t.thesis && <div><span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>THESIS:</span> <span style={{ color: 'var(--text-secondary)' }}>{t.thesis}</span></div>}
                      </div>
                    )}
                 </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
