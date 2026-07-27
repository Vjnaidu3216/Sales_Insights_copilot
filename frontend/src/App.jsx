import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, BarChart3, Database, Bot, Zap, Search, RefreshCw, 
  ArrowUpRight, ArrowDownRight, Layers, CheckCircle2, AlertCircle, 
  Send, Sparkles, Filter, Code2, Users, ShoppingBag, ShieldCheck, DollarSign
} from 'lucide-react';
import { 
  ResponsiveContainer, AreaChart, Area, BarChart, Bar, LineChart, Line, 
  XAxis, YAxis, Tooltip, CartesianGrid, Legend, PieChart, Pie, Cell 
} from 'recharts';

const API_BASE = 'http://127.0.0.1:5000/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('powerbi');
  const [kpis, setKpis] = useState(null);
  const [chartsData, setChartsData] = useState(null);
  const [lineage, setLineage] = useState(null);
  const [loading, setLoading] = useState(true);

  // Power Apps state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);

  // Power Automate state
  const [triggeringFlow, setTriggeringFlow] = useState(false);
  const [flowHistory, setFlowHistory] = useState([
    { id: 'FL-802', time: '10:00 AM', trigger: 'Scheduled Refresh', status: 'Success', records: 0 },
    { id: 'FL-801', time: 'Yesterday', trigger: 'CSV File Arrival', status: 'Success', records: 850 }
  ]);

  // Copilot Studio state
  const [chatMessages, setChatMessages] = useState([
    {
      sender: 'bot',
      text: "Hello! I'm your **Sales Insight Copilot** powered by Copilot Studio & Python ML.\nHow can I assist your sales team today?",
      sql: null,
      type: 'greeting'
    }
  ]);
  const [inputMsg, setInputMsg] = useState('');
  const [chatLoading, setChatLoading] = useState(false);

  // Initial Data Fetch
  const fetchData = async () => {
    setLoading(true);
    try {
      const [kpiRes, chartRes, lineageRes] = await Promise.all([
        fetch(`${API_BASE}/kpis`),
        fetch(`${API_BASE}/charts`),
        fetch(`${API_BASE}/data-lineage`)
      ]);
      const kpiData = await kpiRes.json();
      const chartData = await chartRes.json();
      const lineageData = await lineageRes.json();

      setKpis(kpiData);
      setChartsData(chartData);
      setLineage(lineageData);
    } catch (err) {
      console.error("Error fetching sales data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Search in Power Apps
  const handleSearch = async (query) => {
    setSearchQuery(query);
    try {
      const res = await fetch(`${API_BASE}/powerapps/search?q=${encodeURIComponent(query)}`);
      const data = await res.json();
      setSearchResults(data);
    } catch (err) {
      console.error("Search error:", err);
    }
  };

  useEffect(() => {
    if (activeTab === 'powerapps' && !searchResults) {
      handleSearch('');
    }
  }, [activeTab]);

  // Trigger Power Automate Flow
  const handleTriggerFlow = async () => {
    setTriggeringFlow(true);
    try {
      const res = await fetch(`${API_BASE}/powerautomate/trigger`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file_name: `Q3_CRM_Import_${Date.now()}.csv`, record_count: 25 })
      });
      const data = await res.json();
      
      // Update history
      const newRun = {
        id: `FL-${Math.floor(Math.random() * 900) + 100}`,
        time: new Date().toLocaleTimeString(),
        trigger: data.trigger,
        status: 'Success',
        records: data.records_inserted
      };
      setFlowHistory([newRun, ...flowHistory]);

      // Refresh dashboard charts & KPIs live
      await fetchData();
    } catch (err) {
      console.error("Flow trigger error:", err);
    } finally {
      setTriggeringFlow(false);
    }
  };

  // Send Copilot Chat Message
  const handleSendChat = async (messageToSend) => {
    const text = messageToSend || inputMsg;
    if (!text.trim()) return;

    const userMsgObj = { sender: 'user', text: text };
    setChatMessages(prev => [...prev, userMsgObj]);
    if (!messageToSend) setInputMsg('');
    setChatLoading(true);

    try {
      const res = await fetch(`${API_BASE}/copilot/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text })
      });
      const botRes = await res.json();

      setChatMessages(prev => [...prev, {
        sender: 'bot',
        text: botRes.answer,
        sql: botRes.sql_executed,
        type: botRes.type,
        table: botRes.table,
        action_items: botRes.action_items,
        data: botRes.data,
        orders: botRes.orders
      }]);
    } catch (err) {
      setChatMessages(prev => [...prev, {
        sender: 'bot',
        text: "Sorry, I encountered an error querying the Sales database.",
        sql: null
      }]);
    } finally {
      setChatLoading(false);
    }
  };

  const COLORS = ['#6366F1', '#06B6D4', '#8B5CF6', '#10B981', '#F59E0B'];

  return (
    <div>
      {/* App Header & Navigation */}
      <header className="app-header">
        <div className="logo-badge">
          <div className="logo-icon">
            <TrendingUp size={24} />
          </div>
          <div className="title-text">
            <h1>Sales Insight Copilot</h1>
            <p>Power Platform • Python ML • SQL Engine • Copilot Studio</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="tab-navigation">
          <button 
            className={`nav-tab ${activeTab === 'powerbi' ? 'active' : ''}`}
            onClick={() => setActiveTab('powerbi')}
          >
            <BarChart3 size={18} />
            <span>Power BI Dashboard</span>
          </button>
          
          <button 
            className={`nav-tab ${activeTab === 'powerapps' ? 'active' : ''}`}
            onClick={() => setActiveTab('powerapps')}
          >
            <ShoppingBag size={18} />
            <span>Power Apps Portal</span>
          </button>

          <button 
            className={`nav-tab ${activeTab === 'powerautomate' ? 'active' : ''}`}
            onClick={() => setActiveTab('powerautomate')}
          >
            <Zap size={18} />
            <span>Power Automate Flow</span>
          </button>

          <button 
            className={`nav-tab ${activeTab === 'copilot' ? 'active' : ''}`}
            onClick={() => setActiveTab('copilot')}
          >
            <Bot size={18} />
            <span>Copilot Studio AI</span>
          </button>
        </nav>
      </header>

      {/* Main App Workspace */}
      <main className="app-container">

        {loading ? (
          <div style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-muted)' }}>
            <RefreshCw size={32} className="spin-icon" style={{ marginBottom: '1rem', animation: 'spin 1s linear infinite' }} />
            <p>Loading Sales Insight Data Engine & ML Models...</p>
          </div>
        ) : (
          <>
            {/* 1. POWER BI DASHBOARD TAB */}
            {activeTab === 'powerbi' && (
              <div>
                {/* KPI Cards Grid */}
                <div className="kpi-grid">
                  <div className="glass-card kpi-card">
                    <div className="kpi-title">
                      <span>Total Sales</span>
                      <DollarSign size={16} color="var(--primary)" />
                    </div>
                    <div className="kpi-val">${kpis?.total_sales?.toLocaleString()}</div>
                    <div className="kpi-sub positive">
                      <ArrowUpRight size={14} /> +18.4% YoY Growth
                    </div>
                  </div>

                  <div className="glass-card kpi-card success">
                    <div className="kpi-title">
                      <span>Total Profit</span>
                      <TrendingUp size={16} color="var(--success)" />
                    </div>
                    <div className="kpi-val">${kpis?.total_profit?.toLocaleString()}</div>
                    <div className="kpi-sub positive">
                      <CheckCircle2 size={14} /> Healthy Margin
                    </div>
                  </div>

                  <div className="glass-card kpi-card info">
                    <div className="kpi-title">
                      <span>Profit Margin</span>
                      <Layers size={16} color="var(--secondary)" />
                    </div>
                    <div className="kpi-val">{kpis?.profit_margin}%</div>
                    <div className="kpi-sub">
                      DAX Formula: DIVIDE([Profit], [Sales])
                    </div>
                  </div>

                  <div className="glass-card kpi-card warning">
                    <div className="kpi-title">
                      <span>Forecast Accuracy</span>
                      <Sparkles size={16} color="var(--warning)" />
                    </div>
                    <div className="kpi-val">+{kpis?.forecast_accuracy}%</div>
                    <div className="kpi-sub positive">
                      <ArrowUpRight size={14} /> +20% Accuracy Boost via ML
                    </div>
                  </div>

                  <div className="glass-card kpi-card">
                    <div className="kpi-title">
                      <span>Next Month Forecast</span>
                      <Bot size={16} color="var(--accent)" />
                    </div>
                    <div className="kpi-val">${kpis?.next_month_forecast?.toLocaleString()}</div>
                    <div className="kpi-sub">
                      Scikit-Learn Regression Prediction
                    </div>
                  </div>
                </div>

                {/* Dashboard Main Visuals */}
                <div className="dashboard-grid">
                  {/* Monthly Trend & Forecast Chart */}
                  <div className="glass-card">
                    <div className="chart-header">
                      <h3><TrendingUp size={18} color="var(--primary)" /> Monthly Sales Trend & Scikit-Learn ML Forecast</h3>
                      <span className="preset-chip">Live ML Model Sync</span>
                    </div>
                    <div className="chart-body" style={{ height: 350 }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={chartsData?.forecast_timeline || []}>
                          <defs>
                            <linearGradient id="colorSales" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#6366F1" stopOpacity={0.4}/>
                              <stop offset="95%" stopColor="#6366F1" stopOpacity={0}/>
                            </linearGradient>
                            <linearGradient id="colorForecast" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.5}/>
                              <stop offset="95%" stopColor="#8B5CF6" stopOpacity={0}/>
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                          <XAxis dataKey="period" stroke="var(--text-muted)" />
                          <YAxis stroke="var(--text-muted)" tickFormatter={(v) => `$${v/1000}k`} />
                          <Tooltip 
                            contentStyle={{ background: '#121A2B', borderColor: 'var(--border-card)', borderRadius: '10px' }}
                            formatter={(value) => value ? [`$${Number(value).toLocaleString()}`, 'Amount'] : ['--', 'Amount']}
                          />
                          <Legend />
                          <Area type="monotone" dataKey="actual_sales" name="Actual Sales ($)" stroke="#6366F1" fillOpacity={1} fill="url(#colorSales)" strokeWidth={2} />
                          <Area type="monotone" dataKey="forecast_sales" name="ML Forecast ($)" stroke="#8B5CF6" strokeDasharray="5 5" fillOpacity={1} fill="url(#colorForecast)" strokeWidth={2} />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  {/* Region Breakdown Visual */}
                  <div className="glass-card">
                    <div className="chart-header">
                      <h3><BarChart3 size={18} color="var(--secondary)" /> Region Profitability</h3>
                    </div>
                    <div className="chart-body" style={{ height: 350 }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={chartsData?.region_breakdown || []} layout="vertical">
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                          <XAxis type="number" stroke="var(--text-muted)" tickFormatter={(v) => `$${v/1000}k`} />
                          <YAxis type="category" dataKey="Region" stroke="var(--text-muted)" width={100} />
                          <Tooltip contentStyle={{ background: '#121A2B', borderColor: 'var(--border-card)', borderRadius: '10px' }} />
                          <Bar dataKey="Sales" name="Sales ($)" fill="#6366F1" radius={[0, 6, 6, 0]} />
                          <Bar dataKey="Profit" name="Profit ($)" fill="#10B981" radius={[0, 6, 6, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </div>

                {/* Secondary Visuals & DAX Inspector */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1.5rem' }}>
                  {/* Top Products */}
                  <div className="glass-card" style={{ padding: '1.25rem' }}>
                    <h4 style={{ color: 'white', marginBottom: '1rem', fontSize: '0.95rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <ShoppingBag size={16} color="var(--accent)" /> Top 5 Revenue Products
                    </h4>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                      {chartsData?.top_products?.map((prod, i) => (
                        <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(255,255,255,0.03)', padding: '0.6rem 0.8rem', borderRadius: '8px' }}>
                          <div>
                            <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'white' }}>{prod.Product}</div>
                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{prod.Quantity} units sold</div>
                          </div>
                          <div style={{ textAlign: 'right' }}>
                            <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#10B981' }}>${prod.Sales?.toLocaleString()}</div>
                            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Profit: ${prod.Profit?.toLocaleString()}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* DAX Formula Inspector */}
                  <div className="glass-card" style={{ padding: '1.25rem' }}>
                    <h4 style={{ color: 'white', marginBottom: '1rem', fontSize: '0.95rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <Code2 size={16} color="var(--primary)" /> Power BI DAX Formulas
                    </h4>
                    <div className="dax-card">
                      <span className="dax-name">Total Sales</span> = <span className="dax-func">SUM</span>(Sales[Sales])
                    </div>
                    <div className="dax-card">
                      <span className="dax-name">Total Profit</span> = <span className="dax-func">SUM</span>(Sales[Profit])
                    </div>
                    <div className="dax-card">
                      <span className="dax-name">Profit Margin</span> = <span className="dax-func">DIVIDE</span>([Total Profit], [Total Sales])
                    </div>
                    <div className="dax-card">
                      <span className="dax-name">Forecast Variance</span> = <span className="dax-func">DIVIDE</span>([Actual Sales] - [ML Forecast], [Actual Sales])
                    </div>
                  </div>

                  {/* Data Lineage & Line of Origin */}
                  <div className="glass-card" style={{ padding: '1.25rem' }}>
                    <h4 style={{ color: 'white', marginBottom: '1rem', fontSize: '0.95rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <ShieldCheck size={16} color="var(--success)" /> Data Quality & Lineage
                    </h4>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                      <div>
                        <strong style={{ color: 'white' }}>Data Source:</strong> {lineage?.source}
                      </div>
                      <div>
                        <strong style={{ color: 'white' }}>Target Database:</strong> {lineage?.target_database} ({lineage?.record_count} verified rows)
                      </div>
                      <div>
                        <strong style={{ color: 'white' }}>Cleaning Steps:</strong>
                        <ul style={{ paddingLeft: '1.2rem', marginTop: '0.25rem' }}>
                          {lineage?.cleaning_pipeline?.map((step, i) => (
                            <li key={i}>{step}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* 2. POWER APPS PORTAL TAB */}
            {activeTab === 'powerapps' && (
              <div>
                <div className="glass-card" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
                    <div>
                      <h2 style={{ fontSize: '1.2rem', fontWeight: 800, color: 'white', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <ShoppingBag color="var(--primary)" /> Power Apps Sales Rep Portal
                      </h2>
                      <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Query customer accounts, search order history, and trigger AI recommendations</p>
                    </div>
                    
                    {/* Search Input */}
                    <div style={{ display: 'flex', gap: '0.5rem', width: '380px' }}>
                      <div style={{ position: 'relative', width: '100%' }}>
                        <Search size={16} style={{ position: 'absolute', left: '12px', top: '12px', color: 'var(--text-muted)' }} />
                        <input 
                          type="text" 
                          placeholder="Search Customer, Product, Salesperson..." 
                          value={searchQuery}
                          onChange={(e) => handleSearch(e.target.value)}
                          className="chat-input"
                          style={{ paddingLeft: '2.4rem' }}
                        />
                      </div>
                    </div>
                  </div>

                  {/* Customer Search Table */}
                  <h4 style={{ fontSize: '0.9rem', color: 'white', marginBottom: '0.75rem' }}>Accounts & Customer Insights</h4>
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Customer Name</th>
                        <th>Total Orders</th>
                        <th>Total Revenue</th>
                        <th>Generated Profit</th>
                        <th>Status / Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {searchResults?.customers?.map((cust, i) => (
                        <tr key={i}>
                          <td style={{ fontWeight: 600, color: 'white' }}>{cust.CustomerName}</td>
                          <td>{cust.OrdersCount || cust.Orders}</td>
                          <td style={{ color: '#10B981', fontWeight: 700 }}>${cust.TotalSales?.toLocaleString()}</td>
                          <td>${cust.TotalProfit?.toLocaleString()}</td>
                          <td>
                            <button 
                              className="preset-chip" 
                              onClick={() => handleSendChat(`Show details for customer ${cust.CustomerName}`)}
                            >
                              Query Copilot AI
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Filtered Orders List if Searching */}
                {searchResults?.filtered_orders?.length > 0 && (
                  <div className="glass-card" style={{ padding: '1.5rem' }}>
                    <h4 style={{ fontSize: '0.9rem', color: 'white', marginBottom: '0.75rem' }}>Recent Order Line Items</h4>
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Order ID</th>
                          <th>Customer</th>
                          <th>Product</th>
                          <th>Region</th>
                          <th>Salesperson</th>
                          <th>Sales</th>
                          <th>Profit</th>
                          <th>Date</th>
                        </tr>
                      </thead>
                      <tbody>
                        {searchResults.filtered_orders.map((ord, i) => (
                          <tr key={i}>
                            <td style={{ fontFamily: 'var(--font-mono)' }}>#{ord.OrderID}</td>
                            <td>{ord.CustomerName}</td>
                            <td>{ord.Product}</td>
                            <td>{ord.Region}</td>
                            <td>{ord.Salesperson}</td>
                            <td style={{ fontWeight: 700, color: 'white' }}>${ord.Sales?.toLocaleString()}</td>
                            <td style={{ color: '#10B981' }}>${ord.Profit?.toLocaleString()}</td>
                            <td style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{ord.OrderDate}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

            {/* 3. POWER AUTOMATE FLOW TAB */}
            {activeTab === 'powerautomate' && (
              <div>
                <div className="glass-card" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                    <div>
                      <h2 style={{ fontSize: '1.2rem', fontWeight: 800, color: 'white', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <Zap color="var(--warning)" /> Power Automate Data Refresh Pipeline
                      </h2>
                      <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Automated cloud workflow triggering on new CRM data files & executing SQL transforms</p>
                    </div>

                    <button 
                      className="btn-primary"
                      onClick={handleTriggerFlow}
                      disabled={triggeringFlow}
                    >
                      {triggeringFlow ? (
                        <>Running Flow Execution...</>
                      ) : (
                        <>
                          <Zap size={16} /> Trigger Automated Ingestion Flow
                        </>
                      )}
                    </button>
                  </div>

                  {/* Flow Diagram */}
                  <div className="flow-container">
                    <div className="flow-step">
                      <div className="flow-step-num">1</div>
                      <div>
                        <div style={{ fontWeight: 700, color: 'white' }}>Trigger: When new CSV file arrives</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Monitors SharePoint / OneDrive sales folder</div>
                      </div>
                    </div>

                    <div className="flow-step">
                      <div className="flow-step-num">2</div>
                      <div>
                        <div style={{ fontWeight: 700, color: 'white' }}>Python Data Cleaning Service</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Deduplication, NaN fill, schema validation</div>
                      </div>
                    </div>

                    <div className="flow-step">
                      <div className="flow-step-num">3</div>
                      <div>
                        <div style={{ fontWeight: 700, color: 'white' }}>Insert Batch into SQL Database</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Executes bulk SQL transaction into Sales table</div>
                      </div>
                    </div>

                    <div className="flow-step">
                      <div className="flow-step-num">4</div>
                      <div>
                        <div style={{ fontWeight: 700, color: 'white' }}>Refresh Power BI Dataset & Scikit-Learn Model</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Calls Power BI REST API & updates ML regression model</div>
                      </div>
                    </div>

                    <div className="flow-step">
                      <div className="flow-step-num">5</div>
                      <div>
                        <div style={{ fontWeight: 700, color: 'white' }}>Send Teams/Email Notification</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Notifies sales leadership with summary KPIs</div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Flow Execution History */}
                <div className="glass-card" style={{ padding: '1.5rem' }}>
                  <h4 style={{ fontSize: '0.9rem', color: 'white', marginBottom: '0.75rem' }}>Flow Run History Logs</h4>
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Flow Run ID</th>
                        <th>Timestamp</th>
                        <th>Trigger Source</th>
                        <th>Records Ingested</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {flowHistory.map((run, i) => (
                        <tr key={i}>
                          <td style={{ fontFamily: 'var(--font-mono)' }}>{run.id}</td>
                          <td>{run.time}</td>
                          <td>{run.trigger}</td>
                          <td style={{ fontWeight: 700, color: 'white' }}>+{run.records} rows</td>
                          <td>
                            <span style={{ background: 'rgba(16,185,129,0.15)', color: '#10B981', padding: '0.25rem 0.6rem', borderRadius: '12px', fontSize: '0.75rem', fontWeight: 600 }}>
                              {run.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* 4. COPILOT STUDIO AI ASSISTANT TAB */}
            {activeTab === 'copilot' && (
              <div className="glass-card copilot-box">
                <div className="chart-header">
                  <h3><Bot size={20} color="var(--primary)" /> Copilot Studio Sales Assistant</h3>
                  <span className="preset-chip" style={{ borderColor: 'var(--success)', color: '#10B981' }}>Agentic Online</span>
                </div>

                {/* Preset Prompt Suggestions */}
                <div style={{ padding: '0.75rem 1.5rem', background: 'rgba(0,0,0,0.2)', borderBottom: '1px solid var(--border-card)', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                    <Sparkles size={14} color="var(--warning)" /> Try asking:
                  </span>
                  <button className="preset-chip" onClick={() => handleSendChat("What were total sales in June?")}>What were total sales in June?</button>
                  <button className="preset-chip" onClick={() => handleSendChat("Which region had highest profit?")}>Which region had highest profit?</button>
                  <button className="preset-chip" onClick={() => handleSendChat("Show forecast for next month")}>Show forecast for next month</button>
                  <button className="preset-chip" onClick={() => handleSendChat("Top 5 customers")}>Top 5 customers</button>
                  <button className="preset-chip" onClick={() => handleSendChat("Show low-performing products")}>Show low-performing products</button>
                </div>

                {/* Chat History */}
                <div className="chat-history">
                  {chatMessages.map((msg, i) => (
                    <div key={i} className={`chat-bubble ${msg.sender}`}>
                      <div style={{ whiteSpace: 'pre-wrap' }}>{msg.text}</div>

                      {/* SQL Execution Badge */}
                      {msg.sql && (
                        <div style={{ marginTop: '0.75rem', padding: '0.5rem 0.75rem', background: 'rgba(0,0,0,0.4)', borderRadius: '8px', borderLeft: '3px solid var(--primary)', fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: '#A5B4FC' }}>
                          <div style={{ fontSize: '0.65rem', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '0.2rem' }}>Executed SQL Query</div>
                          {msg.sql}
                        </div>
                      )}

                      {/* Structured Table Response */}
                      {msg.table && (
                        <table className="data-table" style={{ marginTop: '0.75rem' }}>
                          <thead>
                            <tr>
                              {Object.keys(msg.table[0] || {}).map((key, idx) => (
                                <th key={idx}>{key}</th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {msg.table.map((row, rIdx) => (
                              <tr key={rIdx}>
                                {Object.values(row).map((val, cIdx) => (
                                  <td key={cIdx}>{val}</td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      )}

                      {/* Action Items Response */}
                      {msg.action_items && (
                        <div style={{ marginTop: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                          {msg.action_items.map((item, aIdx) => (
                            <div key={aIdx} style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', padding: '0.75rem', borderRadius: '8px' }}>
                              <div style={{ fontWeight: 700, color: 'white' }}>{item.product}</div>
                              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Sales: {item.sales} • Profit: {item.profit} ({item.margin} margin)</div>
                              <div style={{ fontSize: '0.8rem', color: '#F87171', marginTop: '0.25rem', fontWeight: 600 }}>⚡ Recommendation: {item.recommendation}</div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}

                  {chatLoading && (
                    <div className="chat-bubble bot" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <RefreshCw size={16} className="spin-icon" style={{ animation: 'spin 1s linear infinite' }} />
                      <span>Copilot is querying SQL DB & ML model...</span>
                    </div>
                  )}
                </div>

                {/* Input Bar */}
                <div className="chat-input-bar">
                  <input 
                    type="text" 
                    placeholder="Ask Copilot a question about sales, forecast, regions, or products..." 
                    value={inputMsg}
                    onChange={(e) => setInputMsg(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSendChat()}
                    className="chat-input"
                  />
                  <button className="btn-primary" onClick={() => handleSendChat()}>
                    <Send size={16} /> Send
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
