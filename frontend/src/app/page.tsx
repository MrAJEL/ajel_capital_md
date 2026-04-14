'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import * as api from '../lib/api';

// Components
import Sidebar from '../components/Sidebar';
import SettingsWindow from '../components/SettingsWindow';
import DashboardView from '../components/DashboardView';
import WatchlistView from '../components/WatchlistView';
import ManagementView from '../components/ManagementView';
import ClientManagement from '../components/ClientManagement';

export default function App() {
  const [status, setStatus] = useState<any>(null);
  const [statusLoading, setStatusLoading] = useState(true);
  
  const [activeTab, setActiveTab] = useState('dashboard');
  const [showSettings, setShowSettings] = useState(false);
  
  // Settings
  const [refreshInterval, setRefreshInterval] = useState(60);
  const [benchmarkSymbol, setBenchmarkSymbol] = useState('SPY');
  const [currency, setCurrency] = useState('USD');

  const [portfolios, setPortfolios] = useState<any[]>([]);
  const [activePortfolio, setActivePortfolio] = useState<number | null>(null);
  
  // Data
  const [activePositions, setActivePositions] = useState<any[]>([]);
  const [portfolioHistory, setPortfolioHistory] = useState<any[]>([]);
  const [transactions, setTransactions] = useState<any[]>([]);
  const [clients, setClients] = useState<any[]>([]);
  const [livePrices, setLivePrices] = useState<Record<string, any>>({});
  
  // Watchlist
  const [watchlistSymbols, setWatchlistSymbols] = useState<string[]>(['AAPL', 'MSFT', 'BTC-USD', 'NVDA', 'TSLA']);
  const [watchlistPrices, setWatchlistPrices] = useState<Record<string, any>>({});
  const [watchlistScores, setWatchlistScores] = useState<Record<string, any>>({});
  const [newSymbol, setNewSymbol] = useState('');
  const [isLoadingPrices, setIsLoadingPrices] = useState(false);
  const [isLoadingScores, setIsLoadingScores] = useState(false);

  // Forms
  const [activeTxnForm, setActiveTxnForm] = useState<any>({
    type: 'BUY', asset_type: 'stock', symbol: '', qty: '', price: '', fees: '', 
    date: '', emotion: '', thesis: '', broker: '', portfolio_id: '', total_amount: ''
  });
  const [isSubmittingTxn, setIsSubmittingTxn] = useState(false);
  const [isCreatingClient, setIsCreatingClient] = useState(false);

  // Refs
  const refreshTimer = useRef<NodeJS.Timeout | null>(null);

  // ── Init API ───────────────────────────────────────────────────────────────
  useEffect(() => {
    api.getStatus()
      .then(res => setStatus(res))
      .catch(err => console.error("API error:", err))
      .finally(() => setStatusLoading(false));

    loadPortfolios();
    loadClients();
    loadWatchlistPrices();
  }, []);

  useEffect(() => {
    if (activePortfolio) {
      loadPortfolioData(activePortfolio);
      loadTransactions(activePortfolio);
    }
  }, [activePortfolio]);

  // Auto-refresh
  useEffect(() => {
    if (refreshTimer.current) clearInterval(refreshTimer.current);
    if (!activePortfolio) return;
    refreshTimer.current = setInterval(() => {
      loadBatchPrices(activePositions.map(p => p.symbol));
      loadWatchlistPrices();
    }, refreshInterval * 1000);
    return () => clearInterval(refreshTimer.current as NodeJS.Timeout);
  }, [refreshInterval, activePositions, watchlistSymbols]);

  // ── Data Loaders ───────────────────────────────────────────────────────────
  const loadPortfolios = async () => {
    try {
       const res = await api.getPortfolios();
       setPortfolios(res.portfolios);
       if (res.portfolios.length > 0 && !activePortfolio) {
         setActivePortfolio(res.portfolios[0].id);
       }
    } catch(e) { console.error('Error loading portfolios', e) }
  };

  const loadPortfolioData = async (id: number) => {
    try {
      const res = await api.getPortfolio(id);
      setActivePositions(res.positions || []);
      setPortfolioHistory(res.history || []);
      if (res.positions && res.positions.length > 0) {
        loadBatchPrices(res.positions.map((p: any) => p.symbol));
      }
    } catch(e) { console.error('Error loading portfolio data', e) }
  };

  const loadTransactions = async (id: number) => {
    try {
       const res = await api.getTransactions(id);
       setTransactions(res.transactions || []);
    } catch(e) { console.error('Error loading transactions', e) }
  };

  const loadClients = async () => {
    try {
       const res = await api.getClients();
       setClients(res.clients || []);
    } catch(e) { console.error('Error loading clients', e) }
  };

  const loadBatchPrices = async (symbols: string[]) => {
    if (!symbols.length) return;
    try {
       const res = await api.getPricesBatch(symbols);
       setLivePrices(prev => ({...prev, ...res.prices}));
    } catch(e) {}
  };

  const loadWatchlistPrices = async () => {
    if (!watchlistSymbols.length) return;
    setIsLoadingPrices(true);
    try {
       const res = await api.getPricesBatch(watchlistSymbols);
       setWatchlistPrices(res.prices || {});
    } catch(e) {} finally { setIsLoadingPrices(false); }
  };

  const loadWatchlistScores = async () => {
    if (!watchlistSymbols.length) return;
    setIsLoadingScores(true);
    try {
       const res = await api.getBatchScores(watchlistSymbols);
       setWatchlistScores(res.scores || {});
    } catch(e) {} finally { setIsLoadingScores(false); }
  };

  // ── Polling Effect ─────────────────────────────────────────────────────────
  useEffect(() => {
    if (!refreshInterval) return;
    const tick = () => {
      // Refresh active portfolio prices
      if (activePositions.length > 0) {
        loadBatchPrices(activePositions.map((p: any) => p.symbol));
      }
      // Refresh watchlist prices
      if (watchlistSymbols.length > 0) {
        loadWatchlistPrices();
      }
    };
    const interval = setInterval(tick, refreshInterval * 1000);
    return () => clearInterval(interval);
  }, [refreshInterval, activePositions, watchlistSymbols]);

  // ── Actions ────────────────────────────────────────────────────────────────
  const handleCreateTransaction = async () => {
    // Use portfolio_id from form, or fallback to activePortfolio
    const portfolioId = activeTxnForm.portfolio_id || activePortfolio;
    if (!portfolioId) return;

    const txType = (activeTxnForm.type || 'BUY').toUpperCase();
    const isDepositLike = ['DEPOSIT', 'WITHDRAWAL', 'FEE'].includes(txType);
    
    // Validate
    if (!isDepositLike && !activeTxnForm.symbol) return;
    if (!isDepositLike && (!activeTxnForm.qty || !activeTxnForm.price)) return;
    if (isDepositLike && !activeTxnForm.total_amount) return;

    setIsSubmittingTxn(true);
    try {
      await api.createTransaction({
        ...activeTxnForm,
        portfolio_id: portfolioId,
        qty: activeTxnForm.qty ? parseFloat(activeTxnForm.qty) : 0,
        price: activeTxnForm.price ? parseFloat(activeTxnForm.price) : 0,
        total_amount: activeTxnForm.total_amount 
          ? parseFloat(activeTxnForm.total_amount)
          : (parseFloat(activeTxnForm.qty || '0') * parseFloat(activeTxnForm.price || '0')),
        fees: parseFloat(activeTxnForm.fees || '0'),
        date: activeTxnForm.date ? new Date(activeTxnForm.date).toISOString() : new Date().toISOString(),
      });
      loadPortfolioData(portfolioId);
      loadTransactions(portfolioId);
      setActiveTxnForm({ 
        type: 'BUY', asset_type: 'stock', symbol: '', qty: '', price: '', fees: '', 
        date: '', emotion: '', thesis: '', broker: '', portfolio_id: portfolioId, total_amount: ''
      });
    } catch(e) { console.error(e) } finally { setIsSubmittingTxn(false) }
  };

  const handleDeleteTransaction = async (id: number) => {
    try {
      await api.deleteTransaction(id);
      if (activePortfolio) {
        loadPortfolioData(activePortfolio);
        loadTransactions(activePortfolio);
      }
    } catch(e) { console.error(e) }
  };

  const handleCreateClient = async (form: any) => {
    setIsCreatingClient(true);
    try {
       await api.createClient(form);
       loadClients();
    } catch (e) {
       console.error(e);
    } finally { setIsCreatingClient(false) }
  };

  const handleDeleteClient = async (id: number) => {
    try {
       await api.deleteClient(id);
       loadClients();
    } catch (e) { console.error(e) }
  };

  const handleCreatePortfolio = async (name: string, clientId?: number) => {
    if (!name) return;
    try {
       await api.createPortfolio({ name, currency: 'USD', client_id: clientId });
       loadPortfolios();
    } catch (e) { console.error(e) }
  };

  // ── Calculations ───────────────────────────────────────────────────────────
  let totalCash = 0;
  let capitalDepositado = 0;

  transactions.forEach((txn: any) => {
      const txType = (txn.type || '').toUpperCase();
      const amount = txn.total_amount || (Math.abs(txn.qty || 0) * Math.abs(txn.price || 0));
      const sym = txn.symbol ? txn.symbol.toUpperCase() : null;
      
      if (txType === 'DEPOSIT') {
          totalCash += amount;
          capitalDepositado += amount;
      } else if (txType === 'WITHDRAWAL') {
          totalCash -= amount;
          capitalDepositado -= amount;
      } else if (txType === 'BUY' && sym) {
          totalCash -= amount;
      } else if (txType === 'SELL' && sym) {
          totalCash += amount;
      }
  });

  let positionsInvested = 0;
  let positionsMarketValue = 0;
  let totalUnrealizedPnL = 0;
  let totalRealizedPnL = 0;

  activePositions.forEach((p: any) => {
    const currentPrice = livePrices[p.symbol]?.price || p.avg_cost;
    const invested = p.avg_cost * p.qty;
    const mv = currentPrice * p.qty;
    positionsInvested += invested;
    positionsMarketValue += mv;
    totalUnrealizedPnL += (mv - invested);
    totalRealizedPnL += (p.realized_pnl || 0);
  });

  const totalInvested = capitalDepositado; // True deposited capital
  const totalMarketValue = totalCash + positionsMarketValue; // True Net Asset Value (NAV)
  
  const pnlPct = totalInvested > 0 ? ((totalMarketValue - totalInvested) / totalInvested) * 100 : 0;

  return (
    <div className="app-container">
      <Sidebar 
        activeTab={activeTab} setActiveTab={setActiveTab}
        status={status} statusLoading={statusLoading}
        setShowSettings={setShowSettings}
      />

      <main className="main-content">
        
        {activeTab === 'dashboard' && (
          <DashboardView 
            totalInvested={totalInvested} totalMarketValue={totalMarketValue}
            totalUnrealizedPnL={totalUnrealizedPnL} totalRealizedPnL={totalRealizedPnL}
            pnlPct={pnlPct} activePositions={activePositions} livePrices={livePrices}
            portfolioHistory={portfolioHistory} transactions={transactions}
            portfolios={portfolios} activePortfolio={activePortfolio}
            setActivePortfolio={setActivePortfolio}
          />
        )}

        {activeTab === 'watchlist' && (
          <WatchlistView 
            watchlistSymbols={watchlistSymbols} watchlistPrices={watchlistPrices} watchlistScores={watchlistScores}
            removeWatchlistSymbol={(s: string) => setWatchlistSymbols(prev => prev.filter(x => x !== s))}
            addWatchlistSymbol={() => {
              if (newSymbol && !watchlistSymbols.includes(newSymbol)) {
                setWatchlistSymbols([...watchlistSymbols, newSymbol]);
                setNewSymbol('');
              }
            }}
            newSymbol={newSymbol} setNewSymbol={setNewSymbol}
            loadWatchlistPrices={loadWatchlistPrices} loadWatchlistScores={loadWatchlistScores}
            isLoadingPrices={isLoadingPrices} isLoadingScores={isLoadingScores}
          />
        )}

        {activeTab === 'journal' && (
          <ManagementView 
            transactions={transactions}
            handleTxnChange={(f: string, v: any) => setActiveTxnForm({ ...activeTxnForm, [f]: v })}
            activeTxnForm={activeTxnForm}
            handleCreateTransaction={handleCreateTransaction} handleDeleteTransaction={handleDeleteTransaction}
            isSubmittingTxn={isSubmittingTxn}
            portfolios={portfolios} clients={clients} activePortfolio={activePortfolio}
            setActivePortfolio={setActivePortfolio}
          />
        )}

        {activeTab === 'clients' && (
          <ClientManagement 
            clients={clients} 
            handleCreateClient={handleCreateClient} handleDeleteClient={handleDeleteClient}
            isCreatingClient={isCreatingClient} onRefreshClients={loadClients}
            portfolios={portfolios}
          />
        )}
      </main>

      {showSettings && (
        <SettingsWindow 
          onClose={() => setShowSettings(false)}
          portfolios={portfolios} activePortfolio={activePortfolio} setActivePortfolio={setActivePortfolio}
          refreshInterval={refreshInterval} setRefreshInterval={setRefreshInterval}
          benchmarkSymbol={benchmarkSymbol} setBenchmarkSymbol={setBenchmarkSymbol}
          currency={currency} setCurrency={setCurrency} status={status}
          handleCreatePortfolio={handleCreatePortfolio} clients={clients}
        />
      )}
    </div>
  );
}
