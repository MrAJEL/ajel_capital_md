import React, { useState } from 'react';
import { X, ExternalLink, Activity, Target, Globe, Zap, FileText } from 'lucide-react';
import * as api from '../lib/api';

export default function WatchlistView({ 
  watchlistSymbols, watchlistPrices, watchlistScores, 
  removeWatchlistSymbol, addWatchlistSymbol, 
  newSymbol, setNewSymbol,
  loadWatchlistPrices, loadWatchlistScores,
  isLoadingPrices, isLoadingScores
}: any) {

  const [selectedAsset, setSelectedAsset] = useState<string | null>(null);
  const [detailedScore, setDetailedScore] = useState<any>(null);
  const [isLoadingDetails, setIsLoadingDetails] = useState(false);

  React.useEffect(() => {
    if (selectedAsset) {
      setDetailedScore(null);
      setIsLoadingDetails(true);
      api.getAssetScore(selectedAsset)
        .then(data => setDetailedScore(data))
        .catch(err => console.error("Error fetching detailed score", err))
        .finally(() => setIsLoadingDetails(false));
    }
  }, [selectedAsset]);

  const getScoreColor = (score: number) => {
    if (score >= 65) return '#10B981';
    if (score >= 50) return '#F59E0B';
    if (score >= 35) return '#FB923C';
    return '#EF4444';
  };

  const VerdictBadge = ({ verdict }: { verdict: string }) => {
    const colors: Record<string, { bg: string; text: string }> = {
      'STRONG BUY': { bg: 'rgba(16,185,129,0.2)', text: '#10B981' },
      'BUY': { bg: 'rgba(16,185,129,0.12)', text: '#34D399' },
      'HOLD': { bg: 'rgba(245,158,11,0.12)', text: '#F59E0B' },
      'CAUTION': { bg: 'rgba(239,68,68,0.08)', text: '#FB923C' },
      'SELL': { bg: 'rgba(239,68,68,0.15)', text: '#EF4444' },
      'STRONG SELL': { bg: 'rgba(239,68,68,0.25)', text: '#DC2626' },
    };
    const c = colors[verdict] || { bg: 'var(--bg-input)', text: 'var(--text-muted)' };
    return (
      <span style={{ fontSize: '0.65rem', padding: '2px 8px', borderRadius: '4px', fontWeight: 700, background: c.bg, color: c.text, letterSpacing: '0.05em' }}>
        {verdict}
      </span>
    );
  };

  const tvSymbol = selectedAsset ? selectedAsset.replace('-', '') : '';

  return (
    <div className="animate-fadeIn">
      {selectedAsset && (
        <div style={{
          position: 'fixed', top: 0, left: 0, width: '100%', height: '100%',
          background: 'rgba(0,0,0,0.7)', zIndex: 2000, display: 'flex', justifyContent: 'center', alignItems: 'center'
        }}>
          <div style={{
            background: 'var(--bg-secondary)', width: '90%', maxWidth: '1000px', height: '85vh',
            borderRadius: '12px', border: '1px solid var(--border)', display: 'flex', flexDirection: 'column',
            overflow: 'hidden', animation: 'slideUp 0.3s ease-out'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem 1.5rem', borderBottom: '1px solid var(--border)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--accent)' }}>{selectedAsset}</h2>
                {watchlistScores[selectedAsset] && <VerdictBadge verdict={watchlistScores[selectedAsset].verdict} />}
              </div>
              <button onClick={() => setSelectedAsset(null)} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}><X size={24} /></button>
            </div>
            
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflowY: 'auto', padding: '1.5rem', gap: '1.5rem' }}>
               <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                 <a href={`https://finance.yahoo.com/quote/${selectedAsset}`} target="_blank" rel="noreferrer" style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--text-primary)', textDecoration: 'none', fontSize: '0.85rem', background: 'var(--bg-input)', padding: '6px 12px', borderRadius: '4px' }}><Globe size={14}/> Yahoo Finance</a>
                 <a href={`https://www.google.com/finance/quote/${selectedAsset.split('-')[0]}:NASDAQ`} target="_blank" rel="noreferrer" style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--text-primary)', textDecoration: 'none', fontSize: '0.85rem', background: 'var(--bg-input)', padding: '6px 12px', borderRadius: '4px' }}><Globe size={14}/> Google Finance</a>
                 <a href={`https://finviz.com/quote.ashx?t=${selectedAsset.split('-')[0]}`} target="_blank" rel="noreferrer" style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--text-primary)', textDecoration: 'none', fontSize: '0.85rem', background: 'var(--bg-input)', padding: '6px 12px', borderRadius: '4px' }}><ExternalLink size={14}/> Finviz</a>
                 <a href={`https://8marketcap.com/`} target="_blank" rel="noreferrer" style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--text-primary)', textDecoration: 'none', fontSize: '0.85rem', background: 'var(--bg-input)', padding: '6px 12px', borderRadius: '4px' }}><ExternalLink size={14}/> 8marketcap</a>
               </div>

               <div style={{ display: 'flex', gap: '1.5rem', height: '400px' }}>
                 <div style={{ flex: 2, background: 'var(--bg-input)', borderRadius: '8px', overflow: 'hidden' }}>
                    <iframe 
                      src={`https://s.tradingview.com/widgetembed/?symbol=${tvSymbol}&interval=D&theme=dark&style=1&timezone=Etc%2FUTC`}
                      width="100%" height="100%" frameBorder="0" allowFullScreen
                    />
                 </div>
                 {watchlistScores[selectedAsset] && !watchlistScores[selectedAsset].error && watchlistScores[selectedAsset].composite != null && (
                   <div style={{ flex: 1, background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '8px', padding: '1.5rem' }}>
                      <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '8px' }}><Target size={18}/> Strategy Verdict</h3>

                      <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '2rem' }}>
                         <div style={{ width: '120px', height: '120px', borderRadius: '50%', border: `8px solid ${getScoreColor(watchlistScores[selectedAsset].composite)}`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column' }}>
                            <span style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--text-primary)' }}>{watchlistScores[selectedAsset].composite}</span>
                            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>SCORE</span>
                         </div>
                      </div>

                      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        <div>
                           <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '4px' }}>
                            <span style={{ color: 'var(--text-secondary)' }}>Technical</span>
                            <span style={{ fontWeight: 600 }}>{watchlistScores[selectedAsset].breakdown?.technical || 0}/40</span>
                          </div>
                          <div style={{ height: '6px', background: 'rgba(59,130,246,0.2)', borderRadius: '3px', overflow: 'hidden' }}>
                            <div style={{ height: '100%', width: `${((watchlistScores[selectedAsset].breakdown?.technical || 0)/40)*100}%`, background: '#3B82F6' }} />
                          </div>
                        </div>
                        <div>
                           <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '4px' }}>
                            <span style={{ color: 'var(--text-secondary)' }}>Fundamental</span>
                            <span style={{ fontWeight: 600 }}>{watchlistScores[selectedAsset].breakdown?.fundamental || 0}/40</span>
                          </div>
                          <div style={{ height: '6px', background: 'rgba(16,185,129,0.2)', borderRadius: '3px', overflow: 'hidden' }}>
                            <div style={{ height: '100%', width: `${((watchlistScores[selectedAsset].breakdown?.fundamental || 0)/40)*100}%`, background: '#10B981' }} />
                          </div>
                        </div>
                        <div>
                           <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '4px' }}>
                            <span style={{ color: 'var(--text-secondary)' }}>Macro</span>
                            <span style={{ fontWeight: 600 }}>{watchlistScores[selectedAsset].breakdown?.macro || 0}/20</span>
                          </div>
                          <div style={{ height: '6px', background: 'rgba(245,158,11,0.2)', borderRadius: '3px', overflow: 'hidden' }}>
                            <div style={{ height: '100%', width: `${((watchlistScores[selectedAsset].breakdown?.macro || 0)/20)*100}%`, background: '#F59E0B' }} />
                          </div>
                        </div>
                      </div>
                   </div>
                 )}
                 {detailedScore && detailedScore.intelligence_report && (
                   <div style={{ flex: 1.5, background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '8px', padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem', overflowY: 'auto' }}>
                      <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}><Zap size={18}/> Phase 2 Analysis & Signals</h3>
                      
                      <div style={{ padding: '1rem', background: 'var(--bg-input)', borderRadius: '8px', borderLeft: `4px solid ${getScoreColor(detailedScore.intelligence_report.composite)}` }}>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px', textTransform: 'uppercase' }}>Actionable Signal ({detailedScore.intelligence_report.conviction} conviction)</div>
                        <div style={{ fontSize: '0.95rem', fontWeight: 500, lineHeight: 1.5, color: 'var(--text-primary)' }}>{detailedScore.intelligence_report.action}</div>
                      </div>

                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                        <div style={{ padding: '0.75rem', background: 'rgba(59,130,246,0.1)', borderRadius: '6px', border: '1px solid rgba(59,130,246,0.2)' }}>
                           <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>RSI (14)</div>
                           <div style={{ fontSize: '1.1rem', fontWeight: 600 }}>{detailedScore.technicals?.rsi_14?.toFixed(2) || 'N/A'}</div>
                        </div>
                        <div style={{ padding: '0.75rem', background: 'rgba(16,185,129,0.1)', borderRadius: '6px', border: '1px solid rgba(16,185,129,0.2)' }}>
                           <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>Trend</div>
                           <div style={{ fontSize: '1.1rem', fontWeight: 600, textTransform: 'capitalize' }}>{detailedScore.technicals?.trend?.replace('_', ' ') || 'N/A'}</div>
                        </div>
                      </div>
                      
                      {detailedScore.fundamentals && detailedScore.fundamentals.pe_ratio && (
                        <div style={{ padding: '1rem', background: 'var(--bg-input)', borderRadius: '8px', border: '1px solid var(--border)' }}>
                           <h4 style={{ fontSize: '0.85rem', color: 'var(--text-primary)', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '6px' }}><FileText size={14}/> Fundamentals Pivot</h4>
                           <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                              <div>
                                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>P/E Ratio</div>
                                <div style={{ fontSize: '0.9rem', fontWeight: 500 }}>{detailedScore.fundamentals.pe_ratio?.toFixed(2) || 'N/A'}</div>
                              </div>
                              <div>
                                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Rev Growth</div>
                                <div style={{ fontSize: '0.9rem', fontWeight: 500 }}>{detailedScore.fundamentals.revenue_growth ? (detailedScore.fundamentals.revenue_growth * 100).toFixed(2) + '%' : 'N/A'}</div>
                              </div>
                           </div>
                        </div>
                      )}
                      
                      {isLoadingDetails && <div style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.8rem', padding: '1rem' }}>Loading detailed signals...</div>}
                   </div>
                 )}
               </div>
            </div>
          </div>
        </div>
      )}

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700, marginBottom: '0.5rem' }}>Watchlist</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Real-time prices & intelligence scores from the backend API</p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button onClick={loadWatchlistPrices} disabled={isLoadingPrices} style={{ padding: '10px 20px', borderRadius: 'var(--radius-sm)', border: 'none', background: 'linear-gradient(135deg, var(--accent), var(--accent-hover))', color: 'white', fontWeight: 600, fontSize: '0.85rem', cursor: 'pointer', transition: 'var(--transition)' }}>
            {isLoadingPrices ? '⏳ Loading...' : '🔄 Refresh Prices'}
          </button>
          <button onClick={loadWatchlistScores} disabled={isLoadingScores} style={{ padding: '10px 20px', borderRadius: 'var(--radius-sm)', border: 'none', background: 'linear-gradient(135deg, #8B5CF6, #6D28D9)', color: 'white', fontWeight: 600, fontSize: '0.85rem', cursor: 'pointer', transition: 'var(--transition)' }}>
            {isLoadingScores ? '⏳ Scoring...' : '🧠 Run Scores'}
          </button>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '8px', marginBottom: '1.5rem' }}>
        <input
          value={newSymbol}
          onChange={e => setNewSymbol(e.target.value.toUpperCase())}
          placeholder="Add symbol (e.g. AAPL, BTC-USD)"
          style={{ width: '300px', padding: '10px 14px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', background: 'var(--bg-input)', color: 'var(--text-primary)', fontSize: '0.85rem', outline: 'none' }}
          onKeyDown={e => e.key === 'Enter' && addWatchlistSymbol()}
        />
        <button onClick={addWatchlistSymbol} style={{ padding: '6px 14px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', background: 'var(--bg-input)', color: 'var(--text-secondary)', cursor: 'pointer' }}>+ Add</button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1rem' }}>
        {watchlistSymbols.map((sym: string) => {
          const p = watchlistPrices[sym];
          const sc = watchlistScores[sym];
          return (
            <div key={sym} onClick={() => setSelectedAsset(sym)} style={{
              padding: '1.25rem', borderRadius: 'var(--radius)', background: 'var(--bg-card)',
              border: '1px solid var(--border)', transition: 'all 0.2s',
              cursor: 'pointer',
              position: 'relative'
            }}>
              <button
                onClick={(e) => { e.stopPropagation(); removeWatchlistSymbol(sym); }}
                style={{
                  position: 'absolute', top: '8px', right: '8px',
                  background: 'none', border: 'none', color: 'var(--text-muted)',
                  cursor: 'pointer', fontSize: '1rem', padding: '4px', zIndex: 10
                }}
              >×</button>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontWeight: 700, fontSize: '1.1rem', color: 'var(--accent)' }}>{sym}</span>
                {sc && <VerdictBadge verdict={sc.verdict} />}
              </div>
              {p ? (
                <>
                  <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>${p.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 4 })}</div>
                  <div style={{ color: p.changePct >= 0 ? 'var(--success)' : 'var(--danger)', fontSize: '0.85rem', fontWeight: 600 }}>
                    {p.change >= 0 ? '▲' : '▼'} {Math.abs(p.change).toFixed(2)} ({p.changePct >= 0 ? '+' : ''}{p.changePct.toFixed(2)}%)
                  </div>
                  {p.cached && <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '4px' }}>cached</div>}
                </>
              ) : (
                <div style={{ height: '50px', background: 'var(--bg-input)', borderRadius: '4px', animation: 'pulse 2s infinite' }} />
              )}
              {sc && (
                <div style={{ marginTop: '10px', paddingTop: '10px', borderTop: '1px solid var(--border)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '6px' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Score</span>
                    <span style={{ fontWeight: 700, color: getScoreColor(sc.composite) }}>{sc.composite}/100</span>
                  </div>
                  <div style={{ display: 'flex', gap: '4px', height: '4px', borderRadius: '2px', overflow: 'hidden' }}>
                    <div style={{ flex: sc.breakdown?.technical || 0, background: '#3B82F6', borderRadius: '2px' }} />
                    <div style={{ flex: sc.breakdown?.fundamental || 0, background: '#10B981', borderRadius: '2px' }} />
                    <div style={{ flex: sc.breakdown?.macro || 0, background: '#F59E0B', borderRadius: '2px' }} />
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
