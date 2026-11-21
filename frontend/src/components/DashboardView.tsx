import React from 'react';
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
  PieChart, Pie, Cell
} from 'recharts';

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#06B6D4', '#F97316', '#14B8A6', '#6366F1'];

export default function DashboardView({ 
  totalInvested, totalMarketValue, totalUnrealizedPnL, totalRealizedPnL, pnlPct,
  activePositions, livePrices, portfolioHistory, transactions, portfolios, activePortfolio, setActivePortfolio
}: any) {

  const KPICard = ({ label, value, sub, color }: any) => (
    <div style={{
      padding: '1.25rem', borderRadius: 'var(--radius)', background: 'var(--bg-card)',
      border: '1px solid var(--border)', transition: 'var(--transition)',
    }}>
      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{label}</div>
      <div style={{ fontSize: '1.4rem', fontWeight: 700, color }}>{value}</div>
      {sub && <div style={{ fontSize: '0.8rem', color, marginTop: '4px' }}>{sub}</div>}
    </div>
  );

  // ── Equity Curve from backend ──────────────────────────────────────
  let equityCurveData: any[] = [];
  if (portfolioHistory && portfolioHistory.length > 0) {
    // Generate daily points for the chart without skipping dates
    // so tooltips are available on every day.
    equityCurveData = portfolioHistory.map((pt: any) => ({
      date: new Date(pt.date + 'T12:00:00Z').toLocaleDateString('es-ES', { month: 'short', day: 'numeric', year: '2-digit' }),
      invested: pt.invested,
      cost: pt.value 
    }));
  }

  const hasCurveData = equityCurveData.length > 0;

  // ── Pie Chart: Portfolio Allocation ─────────────────────────────────────
  const pieData = activePositions
    .filter((p: any) => p.qty > 0)
    .map((p: any) => {
      const lp = livePrices[p.symbol];
      const currentPrice = lp?.price || p.avg_cost;
      const mv = p.qty * currentPrice;
      return { name: p.symbol, value: Math.round(mv * 100) / 100 };
    })
    .sort((a: any, b: any) => b.value - a.value);

  const totalPieValue = pieData.reduce((s: number, d: any) => s + d.value, 0);

  // Return Calcs Engine
  // Ratios are undefined with fewer than 2 points or (near-)zero volatility;
  // show "—" instead of dividing by a tiny epsilon.
  const NO_DATA = '—';
  const MIN_STD = 1e-6;
  const calcSharpe = (curve: any[]) => {
    if (curve.length < 2) return NO_DATA;
    let rets = [];
    for(let i=1; i<curve.length; i++) {
        const prev = curve[i-1].invested + curve[i-1].cost;
        const curr = curve[i].invested + curve[i].cost;
        rets.push(prev > 0 ? (curr - prev) / prev : 0);
    }
    const mean = rets.reduce((a,b)=>a+b,0) / rets.length;
    const std = Math.sqrt(rets.reduce((a,b)=>a+Math.pow(b-mean,2),0) / rets.length);
    if (!Number.isFinite(std) || std < MIN_STD) return NO_DATA;
    return (((mean - 0.04/252) / std) * Math.sqrt(252)).toFixed(2);
  };

  const calcSortino = (curve: any[]) => {
    if (curve.length < 2) return NO_DATA;
    let rets = [];
    for(let i=1; i<curve.length; i++) {
        const prev = curve[i-1].invested + curve[i-1].cost;
        const curr = curve[i].invested + curve[i].cost;
        rets.push(prev > 0 ? (curr - prev) / prev : 0);
    }
    const mean = rets.reduce((a,b)=>a+b,0) / rets.length;
    const downRets = rets.filter(r => r < 0);
    if (downRets.length === 0) return NO_DATA;
    const downStd = Math.sqrt(downRets.reduce((a,b)=>a+Math.pow(b,2),0) / downRets.length);
    if (!Number.isFinite(downStd) || downStd < MIN_STD) return NO_DATA;
    return (((mean - 0.04/252) / downStd) * Math.sqrt(252)).toFixed(2);
  };

  const calcMaxDrawdown = (curve: any[]) => {
    if (curve.length < 2) return NO_DATA;
    let peak = 0;
    let maxDd = 0;
    for(let pt of curve) {
      const val = pt.invested + pt.cost;
      if (val > peak) peak = val;
      if (peak > 0) {
        const dd = (peak - val) / peak;
        if (dd > maxDd) maxDd = dd;
      }
    }
    return `${(maxDd * 100).toFixed(2)}%`;
  };

  const driftAlerts = (pie: any[]) => {
     let c = 0;
     const avgWeight = 100 / (pie.length || 1);
     pie.forEach(p => {
       const w = (p.value / (totalInvested || 1)) * 100;
       if (Math.abs(w - avgWeight) > 15) c++;
     });
     return c;
  };

  // ── Helpers ─────────────────────────────────────────────────────────────
  const getDaysSince = (dateStr: string) => {
    if (!dateStr) return 'N/A';
    const diff = new Date().getTime() - new Date(dateStr).getTime();
    return Math.floor(diff / (1000 * 3600 * 24));
  };
  const getDaysBadge = (days: number) => {
    if (days <= 7) return { bg: 'rgba(16,185,129,0.15)', color: '#10B981' };
    if (days <= 30) return { bg: 'rgba(245,158,11,0.15)', color: '#F59E0B' };
    return { bg: 'rgba(239,68,68,0.15)', color: '#EF4444' };
  };

  const renderCustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent, name }: any) => {
    if (percent < 0.05) return null;
    const RADIAN = Math.PI / 180;
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);
    return (
      <text x={x} y={y} fill="white" textAnchor="middle" dominantBaseline="central" fontSize={11} fontWeight={600}>
        {name}
      </text>
    );
  };

  return (
    <div className="animate-fadeIn">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2rem' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700, marginBottom: '0.5rem' }}>Dashboard</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Portfolio overview and market intelligence</p>
        </div>
        
        {/* Portfolio Selector */}
        {portfolios && portfolios.length > 0 && (
          <select 
            value={activePortfolio || ''} 
            onChange={e => setActivePortfolio && setActivePortfolio(Number(e.target.value))}
            style={{ 
              padding: '10px 16px', background: 'var(--bg-input)', border: '1px solid var(--border)', 
              borderRadius: '8px', color: 'white', fontWeight: 500, cursor: 'pointer', outline: 'none'
            }}
          >
            {portfolios.map((p: any) => (
              <option key={p.id} value={p.id}>
                {p.client_name ? `${p.name} — ${p.client_name}` : `${p.name} (Pool)`}
              </option>
            ))}
          </select>
        )}
      </div>

      {/* ── KPI Cards ──────────────────────────────────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
        <KPICard label="Capital Invertido" value={`$${totalInvested.toLocaleString(undefined, { minimumFractionDigits: 2 })}`} color="var(--accent)" />
        <KPICard label="Valor de Mercado" value={`$${totalMarketValue.toLocaleString(undefined, { minimumFractionDigits: 2 })}`} color="var(--gold)" />
        <KPICard label="P&L No Realizado"
          value={`${totalUnrealizedPnL >= 0 ? '+' : ''}$${totalUnrealizedPnL.toLocaleString(undefined, { minimumFractionDigits: 2 })}`}
          sub={`${pnlPct >= 0 ? '+' : ''}${pnlPct.toFixed(2)}%`}
          color={totalUnrealizedPnL >= 0 ? 'var(--success)' : 'var(--danger)'} />
        <KPICard label="P&L Realizado"
          value={`${totalRealizedPnL >= 0 ? '+' : ''}$${totalRealizedPnL.toLocaleString(undefined, { minimumFractionDigits: 2 })}`}
          color={totalRealizedPnL >= 0 ? 'var(--success)' : 'var(--danger)'} />
      </div>

      {/* ── Advanced Metrics ─────────────────────────────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
        <div style={{ padding: '1rem', background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 'var(--radius)' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Sharpe Ratio</div>
          <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'white' }}>{calcSharpe(equityCurveData)}</div>
        </div>
        <div style={{ padding: '1rem', background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 'var(--radius)' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Sortino Ratio</div>
          <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'white' }}>{calcSortino(equityCurveData)}</div>
        </div>
        <div style={{ padding: '1rem', background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 'var(--radius)' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Max Drawdown</div>
          <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--danger)' }}>{calcMaxDrawdown(equityCurveData)}</div>
        </div>
        <div style={{ padding: '1rem', background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 'var(--radius)' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Rebalance Alerts</div>
          <div style={{ fontSize: '1.25rem', fontWeight: 700, color: driftAlerts(pieData) > 0 ? 'var(--warning)' : 'var(--success)' }}>
            {driftAlerts(pieData)} Drifted
          </div>
        </div>
      </div>

      {/* ── Pie Chart + Equity Curve side by side ──────────────────────────── */}
      <div className={pieData.length > 0 ? "grid-cols-pie" : ""} style={{ marginBottom: '2rem' }}>
        
        {/* Allocation Pie */}
        {pieData.length > 0 && (
          <div style={{ padding: '1.25rem', borderRadius: 'var(--radius)', background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.75rem', color: 'var(--text-primary)' }}>🥧 Allocation</h3>
            <div style={{ height: '220px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="50%" innerRadius={50} outerRadius={90}
                    paddingAngle={2} dataKey="value" labelLine={false} label={renderCustomLabel}>
                    {pieData.map((_: any, i: number) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} stroke="none" />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1A202C', borderColor: '#4A5568', color: '#fff', borderRadius: '8px', fontSize: '0.85rem' }}
                    formatter={(value: any, name: any) => [`$${Number(value).toLocaleString()}`, name]}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            {/* Legend */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '0.5rem', justifyContent: 'center' }}>
              {pieData.map((d: any, i: number) => {
                const pct = totalPieValue > 0 ? ((d.value / totalPieValue) * 100).toFixed(1) : '0.0';
                return (
                  <div key={d.name} style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem' }}>
                    <div style={{ width: '8px', height: '8px', borderRadius: '2px', background: COLORS[i % COLORS.length] }} />
                    <span style={{ color: 'var(--text-secondary)' }}>{d.name}</span>
                    <span style={{ color: 'var(--text-muted)' }}>{pct}%</span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Equity Curve */}
        <div style={{ padding: '1.25rem', borderRadius: 'var(--radius)', background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '1rem', color: 'var(--text-primary)' }}>📈 Curva de Capital</h3>
          {!hasCurveData ? (
            <div style={{ height: '260px', width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
              Sin datos
            </div>
          ) : (
          <div style={{ height: '260px', width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={equityCurveData}>
                <defs>
                  <linearGradient id="gradInvested" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3}/><stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="gradCost" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10B981" stopOpacity={0.3}/><stop offset="95%" stopColor="#10B981" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#2D3748" vertical={false} />
                <XAxis dataKey="date" stroke="#A0AEC0" tick={{ fill: '#A0AEC0', fontSize: 12 }} />
                <YAxis stroke="#A0AEC0" tick={{ fill: '#A0AEC0', fontSize: 12 }} tickFormatter={(t) => `$${(t/1000).toFixed(0)}k`} />
                <Tooltip contentStyle={{ backgroundColor: '#1A202C', borderColor: '#4A5568', color: '#fff', borderRadius: '8px' }}
                  formatter={((v: any, n: any) => [`$${Number(v).toLocaleString()}`, n === 'invested' ? 'Capital Depositado' : 'Valor de Mercado']) as any} />
                <Legend formatter={(v: string) => v === 'invested' ? 'Capital Depositado' : 'Valor de Mercado'} />
                <Area type="monotone" dataKey="invested" stroke="#3B82F6" strokeWidth={2} fill="url(#gradInvested)" />
                <Area type="monotone" dataKey="cost" stroke="#10B981" strokeWidth={2} fill="url(#gradCost)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          )}
        </div>
      </div>

      {/* ── Positions Table ────────────────────────────────────────────────── */}
      {activePositions.length > 0 && (
        <div style={{ padding: '1.25rem', borderRadius: 'var(--radius)', background: 'var(--bg-card)', border: '1px solid var(--border)', marginBottom: '2rem' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '1rem', color: 'var(--text-primary)' }}>📊 Posiciones Activas</h3>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
              <thead>
                <tr>
                  {['Symbol', 'Tipo', 'Qty', 'Avg Cost', 'Actual', 'Valor Mercado', 'Peso %', 'P&L', 'Días'].map(h => (
                    <th key={h} style={{ textAlign: 'left', padding: '10px 12px', borderBottom: '1px solid var(--border)', color: 'var(--text-muted)', fontSize: '0.75rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {activePositions.filter((p: any) => p.qty > 0).map((p: any) => {
                  const lp = livePrices[p.symbol];
                  const currentPrice = lp?.price || p.avg_cost;
                  const hasLive = !!lp?.price;
                  const mv = p.qty * currentPrice;
                  const pnl = (currentPrice - p.avg_cost) * p.qty;
                  const pnlP = p.avg_cost > 0 ? ((currentPrice - p.avg_cost) / p.avg_cost * 100) : 0;
                  const wPct = totalMarketValue > 0 ? (mv / totalMarketValue * 100) : 0;
                  const days = getDaysSince(p.last_transaction_at || p.first_buy_date);
                  const badge = typeof days === 'number' ? getDaysBadge(days) : { bg: 'var(--bg-input)', color: 'var(--text-muted)' };
                  return (
                    <tr key={p.id} style={{ transition: 'background 0.2s' }}>
                      <td style={{ padding: '10px 12px', borderBottom: '1px solid rgba(31,42,71,0.5)' }}>
                        <span style={{ fontWeight: 700, color: 'var(--accent)', letterSpacing: '0.04em' }}>{p.symbol}</span>
                      </td>
                      <td style={{ padding: '10px 12px', borderBottom: '1px solid rgba(31,42,71,0.5)' }}>
                        <span style={{ fontSize: '0.7rem', padding: '2px 8px', borderRadius: '4px', background: 'rgba(59,130,246,0.1)', color: 'var(--accent)', textTransform: 'uppercase' }}>{p.asset_type || 'stock'}</span>
                      </td>
                      <td style={{ padding: '10px 12px', borderBottom: '1px solid rgba(31,42,71,0.5)', color: 'var(--text-secondary)' }}>{p.qty.toFixed(4)}</td>
                      <td style={{ padding: '10px 12px', borderBottom: '1px solid rgba(31,42,71,0.5)', color: 'var(--text-secondary)' }}>${p.avg_cost.toFixed(2)}</td>
                      <td style={{ padding: '10px 12px', borderBottom: '1px solid rgba(31,42,71,0.5)' }}>
                        <span style={{ color: hasLive ? 'var(--text-primary)' : 'var(--text-muted)', fontWeight: hasLive ? 600 : 400 }}>
                          ${currentPrice.toFixed(2)}{!hasLive && <span style={{ fontSize: '0.65rem' }}> est</span>}
                        </span>
                      </td>
                      <td style={{ padding: '10px 12px', borderBottom: '1px solid rgba(31,42,71,0.5)', color: 'var(--text-primary)', fontWeight: 500 }}>
                        ${mv.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </td>
                      <td style={{ padding: '10px 12px', borderBottom: '1px solid rgba(31,42,71,0.5)' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <div style={{ width: '40px', height: '4px', background: 'var(--bg-input)', borderRadius: '2px', overflow: 'hidden' }}>
                            <div style={{ width: `${Math.min(wPct, 100)}%`, height: '100%', background: COLORS[activePositions.indexOf(p) % COLORS.length], borderRadius: '2px' }} />
                          </div>
                          <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>{wPct.toFixed(1)}%</span>
                        </div>
                      </td>
                      <td style={{ padding: '10px 12px', borderBottom: '1px solid rgba(31,42,71,0.5)', color: pnl >= 0 ? 'var(--success)' : 'var(--danger)', fontWeight: 600 }}>
                        {pnl >= 0 ? '+' : ''}{pnl.toFixed(2)} <span style={{ fontSize: '0.75rem', opacity: 0.8 }}>({pnlP >= 0 ? '+' : ''}{pnlP.toFixed(1)}%)</span>
                      </td>
                      <td style={{ padding: '10px 12px', borderBottom: '1px solid rgba(31,42,71,0.5)' }}>
                        <span style={{ fontSize: '0.75rem', padding: '2px 8px', borderRadius: '4px', background: badge.bg, color: badge.color, fontWeight: 600 }}>
                          {typeof days === 'number' ? `${days}d` : days}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── Recent Transactions ──────────────────────────────────────────── */}
      {transactions && transactions.length > 0 && (
        <div style={{ padding: '1.25rem', borderRadius: 'var(--radius)', background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '1rem', color: 'var(--text-primary)' }}>📝 Últimas Transacciones</h3>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
              <thead>
                <tr>
                  {['Fecha', 'Tipo', 'Symbol', 'Qty', 'Precio', 'Total', 'Comisiones', 'Emoción', 'Tesis'].map(h => (
                    <th key={h} style={{ textAlign: 'left', padding: '8px 10px', borderBottom: '1px solid var(--border)', color: 'var(--text-muted)', fontSize: '0.7rem', fontWeight: 600, textTransform: 'uppercase' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {transactions.slice(0, 15).map((t: any) => {
                  const total = t.total_amount || ((t.qty || 0) * (t.price || 0));
                  return (
                    <tr key={t.id}>
                      <td style={{ padding: '8px 10px', borderBottom: '1px solid rgba(31,42,71,0.5)', color: 'var(--text-muted)', fontSize: '0.8rem' }}>{t.date ? new Date(t.date).toLocaleDateString() : '—'}</td>
                      <td style={{ padding: '8px 10px', borderBottom: '1px solid rgba(31,42,71,0.5)' }}>
                        <span style={{ padding: '2px 6px', borderRadius: '4px', fontSize: '0.7rem', fontWeight: 700,
                          background: t.type === 'BUY' ? 'rgba(16,185,129,0.1)' : t.type === 'SELL' ? 'rgba(239,68,68,0.1)' : t.type === 'DEPOSIT' ? 'rgba(59,130,246,0.1)' : 'rgba(160,174,192,0.1)',
                          color: t.type === 'BUY' ? '#10B981' : t.type === 'SELL' ? '#EF4444' : t.type === 'DEPOSIT' ? '#3B82F6' : 'var(--text-secondary)' }}>{t.type}</span>
                      </td>
                      <td style={{ padding: '8px 10px', borderBottom: '1px solid rgba(31,42,71,0.5)', fontWeight: 600, color: 'var(--accent)' }}>{t.symbol || '—'}</td>
                      <td style={{ padding: '8px 10px', borderBottom: '1px solid rgba(31,42,71,0.5)', color: 'var(--text-secondary)' }}>{t.qty ? t.qty.toFixed(2) : '—'}</td>
                      <td style={{ padding: '8px 10px', borderBottom: '1px solid rgba(31,42,71,0.5)', color: 'var(--text-secondary)' }}>{t.price ? `$${t.price.toFixed(2)}` : '—'}</td>
                      <td style={{ padding: '8px 10px', borderBottom: '1px solid rgba(31,42,71,0.5)', fontWeight: 600, color: 'var(--text-primary)' }}>${total.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                      <td style={{ padding: '8px 10px', borderBottom: '1px solid rgba(31,42,71,0.5)', color: 'var(--text-muted)' }}>{t.fees > 0 ? `$${t.fees.toFixed(2)}` : '—'}</td>
                      <td style={{ padding: '8px 10px', borderBottom: '1px solid rgba(31,42,71,0.5)' }}>{t.emotion ? <span style={{ color: 'var(--gold)', textTransform: 'capitalize', fontSize: '0.8rem' }}>{t.emotion}</span> : '—'}</td>
                      <td style={{ padding: '8px 10px', borderBottom: '1px solid rgba(31,42,71,0.5)', color: 'var(--text-secondary)', maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: '0.8rem' }}>{t.thesis || '—'}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
