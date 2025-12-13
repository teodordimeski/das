import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import './SymbolDetail.css';

const formatISO = (date) => date.toISOString().split('T')[0];
const formatLabel = (isoDate) =>
  new Date(isoDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });

// Extract base symbol (e.g., "BTCUSDT" -> "BTC")
const getBaseSymbol = (symbol) => {
  if (!symbol) return '';
  const upper = symbol.toUpperCase();
  // Remove common quote assets
  return upper.replace(/USDT$|USDC$|BUSD$|BTC$|ETH$/, '') || upper;
};

const SymbolDetail = () => {
  const { symbol } = useParams();
  const selectedSymbol = (symbol || '').toUpperCase();

  const defaultRange = useMemo(() => {
    const today = new Date();
    const from = new Date();
    from.setDate(today.getDate() - 29);
    return {
      from: formatISO(from),
      to: formatISO(today),
    };
  }, [selectedSymbol]);

  const [formRange, setFormRange] = useState(defaultRange);
  const [activeRange, setActiveRange] = useState(defaultRange);
  const [tableData, setTableData] = useState([]);
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [timeframe, setTimeframe] = useState('MONTHLY');
  const [technicalData, setTechnicalData] = useState(null);
  const [loadingTechnical, setLoadingTechnical] = useState(false);
  const [technicalError, setTechnicalError] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [loadingPrediction, setLoadingPrediction] = useState(false);
  const [predictionError, setPredictionError] = useState(null);

  // Effect for symbol change - reset date range and fetch data
  useEffect(() => {
    setFormRange(defaultRange);
    fetchSymbolData(defaultRange.from, defaultRange.to);
    fetchTechnicalData();
    fetchPrediction();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedSymbol, defaultRange.from, defaultRange.to]);

  // Effect for timeframe change - only refetch technical data, don't reset date range
  useEffect(() => {
    fetchTechnicalData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [timeframe]);

  const fetchSymbolData = async (from, to) => {
    if (!from || !to) {
      setError('Please select both start and end dates.');
      return;
    }

    if (new Date(from) > new Date(to)) {
      setError('Start date must be before end date.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const url = `http://localhost:8080/api/symbol/${selectedSymbol}?from=${from}&to=${to}`;
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error('Unable to load data for the selected symbol.');
      }

      const data = await response.json();
      const sorted = data.sort((a, b) => new Date(a.date) - new Date(b.date));

      const chartReady = sorted.map((entry) => ({
        isoDate: entry.date,
        dateLabel: formatLabel(entry.date),
        close: entry.close ?? 0,
      }));

      setTableData(sorted);
      setChartData(chartReady);
      setActiveRange({ from, to });
    } catch (err) {
      setError(err.message || 'Something went wrong while fetching data.');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadCsv = () => {
    if (!tableData.length) return;

    const headers = [
      'Date',
      'Open',
      'High',
      'Low',
      'Close',
      'Volume',
      'QuoteAssetVolume',
      'Symbol',
      'LastPrice_24h',
      'Volume_24h',
      'QuoteVolume_24h',
      'High_24h',
      'Low_24h',
      'BaseAsset',
      'QuoteAsset',
      'SymbolUsed',
    ];

    const rows = tableData.map((entry) => [
      entry.date,
      entry.open ?? '',
      entry.high ?? '',
      entry.low ?? '',
      entry.close ?? '',
      entry.volume ?? entry.volume_24h ?? '',
      entry.quoteAssetVolume ?? '',
      entry.symbol ?? '',
      entry.lastPrice_24h ?? '',
      entry.volume_24h ?? '',
      entry.quoteVolume_24h ?? '',
      entry.high_24h ?? '',
      entry.low_24h ?? '',
      entry.baseAsset ?? '',
      entry.quoteAsset ?? '',
      entry.symbolUsed ?? '',
    ]);

    const csvContent = [headers, ...rows]
      .map((row) =>
        row
          .map((cell) => {
            const value = cell ?? '';
            if (typeof value === 'number') return value;
            const escaped = String(value).replace(/"/g, '""');
            return `"${escaped}"`;
          })
          .join(','),
      )
      .join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `${selectedSymbol || 'symbol'}-data.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleInputChange = (event) => {
    const { name, value } = event.target;
    setFormRange((prev) => ({ ...prev, [name]: value }));
  };

  const handleApplyRange = () => {
    fetchSymbolData(formRange.from, formRange.to);
  };

  const fetchTechnicalData = async () => {
    if (!selectedSymbol) return;

    setLoadingTechnical(true);
    setTechnicalError(null);
    try {
      const url = `http://localhost:8080/api/technical/${selectedSymbol}?timeframe=${timeframe}`;
      const response = await fetch(url);

      if (!response.ok) {
        let errorMessage = 'Unable to load technical analysis data.';
        if (response.status === 400) {
          errorMessage = 'Insufficient data for technical analysis. Need at least 50 data points.';
        } else if (response.status === 404) {
          errorMessage = 'Symbol not found or no data available.';
        } else if (response.status >= 500) {
          errorMessage = 'Server error. Please try again later.';
        }
        throw new Error(errorMessage);
      }

      const data = await response.json();
      setTechnicalData(data);
      setTechnicalError(null);
    } catch (err) {
      console.error('Error fetching technical data:', err);
      setTechnicalData(null);
      setTechnicalError(err.message || 'Unable to load technical analysis data.');
    } finally {
      setLoadingTechnical(false);
    }
  };

  const fetchPrediction = async () => {
    if (!selectedSymbol) return;

    setLoadingPrediction(true);
    setPredictionError(null);
    try {
      // Extract base symbol (e.g., "BTCUSDT" -> "BTC")
      const baseSymbol = getBaseSymbol(selectedSymbol);
      const url = `http://localhost:8080/api/predictions/${baseSymbol}`;
      const response = await fetch(url);

      if (!response.ok) {
        let errorMessage = 'Unable to load prediction.';
        if (response.status === 400) {
          errorMessage = 'Model not trained or insufficient data.';
        } else if (response.status === 404) {
          errorMessage = 'Symbol not found.';
        } else if (response.status >= 500) {
          errorMessage = 'Server error. Please try again later.';
        }
        throw new Error(errorMessage);
      }

      const data = await response.json();
      setPrediction(data);
      setPredictionError(null);
    } catch (err) {
      console.error('Error fetching prediction:', err);
      setPrediction(null);
      setPredictionError(err.message || 'Unable to load prediction.');
    } finally {
      setLoadingPrediction(false);
    }
  };

  const getSignalClass = (signal) => {
    if (!signal) return 'neutral';
    const upper = signal.toUpperCase();
    if (upper.includes('STRONG_BUY') || upper === 'BUY') return 'buy';
    if (upper.includes('STRONG_SELL') || upper === 'SELL') return 'sell';
    return 'neutral';
  };

  const getSignalColor = (signal) => {
    const signalClass = getSignalClass(signal);
    if (signalClass === 'buy') return '#4ade80';
    if (signalClass === 'sell') return '#f87171';
    return 'rgba(255, 255, 255, 0.6)';
  };

  const calculateGaugeAngle = (buyCount, sellCount, neutralCount) => {
    const total = buyCount + sellCount + neutralCount;
    if (total === 0) return 50; // Default to middle
    const buyRatio = buyCount / total;
    const sellRatio = sellCount / total;
    const neutralRatio = neutralCount / total;
    
    // Gauge arc goes from 0 to 180 degrees
    // Calculate percentage: buy pushes toward 180, sell toward 0, neutral is 90
    const anglePercent = (buyRatio * 180 + sellRatio * 0 + neutralRatio * 90);
    return Math.max(0, Math.min(180, anglePercent));
  };

  const latestEntry = tableData[tableData.length - 1];
  const firstEntry = tableData[0];
  const totalVolume =
    tableData.reduce((sum, entry) => sum + (entry.volume ?? entry.volume_24h ?? 0), 0) || 0;
  const avgVolume = tableData.length ? totalVolume / tableData.length : 0;
  const priceChange =
    firstEntry && latestEntry && firstEntry.close
      ? ((latestEntry.close - firstEntry.close) / firstEntry.close) * 100
      : 0;

  return (
    <div className="symbol-detail">
      <div className="symbol-detail-container">
        <header className="symbol-detail-header">
          <div>
            <p className="symbol-detail-eyebrow">Crypto review</p>
            <h1>{selectedSymbol || 'Symbol'}</h1>
            {activeRange.from && activeRange.to && (
              <p className="symbol-detail-range">
                Showing data from {activeRange.from} to {activeRange.to}
              </p>
            )}
          </div>
          <Link to="/" className="back-button">
            ← Back to homepage
          </Link>
        </header>

        <section className="symbol-detail-stats">
          <div className="stat-card">
            <p className="stat-label">Latest close</p>
            <p className="stat-value">
              {latestEntry?.close ? `$${latestEntry.close.toFixed(2)}` : 'N/A'}
            </p>
            <span className={`stat-pill ${priceChange >= 0 ? 'positive' : 'negative'}`}>
              {priceChange >= 0 ? '+' : ''}
              {priceChange.toFixed(2)}%
            </span>
          </div>
          <div className="stat-card">
            <p className="stat-label">Predicted close</p>
            <p className="stat-value">
              {loadingPrediction ? (
                'Loading...'
              ) : predictionError ? (
                'N/A'
              ) : prediction?.predicted_close ? (
                `$${prediction.predicted_close.toFixed(2)}`
              ) : (
                'N/A'
              )}
            </p>
            <span className="stat-pill neutral">
              {loadingPrediction ? 'Calculating...' : predictionError ? 'Error' : 'LSTM Prediction'}
            </span>
          </div>
          <div className="stat-card">
            <p className="stat-label">Average daily volume</p>
            <p className="stat-value">${avgVolume.toLocaleString(undefined, { maximumFractionDigits: 0 })}</p>
            <span className="stat-pill neutral">Volume (last {tableData.length || 0} days)</span>
          </div>
          <div className="stat-card">
            <p className="stat-label">Highest high</p>
            <p className="stat-value">
              {tableData.length
                ? `$${Math.max(...tableData.map((entry) => entry.high || 0)).toFixed(2)}`
                : 'N/A'}
            </p>
            <span className="stat-pill neutral">30-day window</span>
          </div>
        </section>

        <section className="symbol-detail-filters">
          <div className="date-picker">
            <label htmlFor="from">From</label>
            <input
              id="from"
              name="from"
              type="date"
              value={formRange.from}
              max={formRange.to}
              onChange={handleInputChange}
            />
          </div>
          <div className="date-picker">
            <label htmlFor="to">To</label>
            <input
              id="to"
              name="to"
              type="date"
              value={formRange.to}
              min={formRange.from}
              max={formatISO(new Date())}
              onChange={handleInputChange}
            />
          </div>
          <button className="apply-button" onClick={handleApplyRange}>
            Continue
          </button>
        </section>

        <section className="symbol-detail-chart">
          <div className="section-header">
            <div>
              <h2>Closing price overview</h2>
              <p>Daily close value for {selectedSymbol} (last {tableData.length || 0} records)</p>
            </div>
          </div>
          <div className="chart-wrapper">
            {loading ? (
              <div className="chart-placeholder">Loading chart...</div>
            ) : error ? (
              <div className="chart-placeholder error">{error}</div>
            ) : chartData.length ? (
              <ResponsiveContainer width="100%" height={320}>
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="volumeGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#4ade80" stopOpacity={0.6} />
                      <stop offset="95%" stopColor="#4ade80" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="4 4" stroke="rgba(255,255,255,0.1)" />
                  <XAxis dataKey="dateLabel" stroke="rgba(255,255,255,0.6)" />
                  <YAxis 
                    stroke="rgba(255,255,255,0.6)"
                    tickFormatter={(value) => `$${value.toFixed(2)}`}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#11141f',
                      border: '1px solid rgba(255,255,255,0.1)',
                      borderRadius: '12px',
                      color: '#fff',
                    }}
                    formatter={(value) => [`$${value.toFixed(2)}`, 'Close']}
                  />
                  <Area
                    type="monotone"
                    dataKey="close"
                    stroke="#4ade80"
                    fill="url(#volumeGradient)"
                    strokeWidth={3}
                    dot={false}
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="chart-placeholder">No data for the selected range.</div>
            )}
          </div>
        </section>

        <section className="technical-analysis-section">
          <div className="section-header">
            <div>
              <h2>Technical Indicators</h2>
              <p>Oscillators and moving averages analysis for {selectedSymbol}</p>
            </div>
            <div className="timeframe-selector">
              <label htmlFor="timeframe">Timeframe:</label>
              <select
                id="timeframe"
                value={timeframe}
                onChange={(e) => {
                  setTimeframe(e.target.value);
                  setTechnicalError(null);
                }}
                className="timeframe-dropdown"
              >
                <option value="DAILY">Day</option>
                <option value="WEEKLY">Week</option>
                <option value="MONTHLY">Month</option>
              </select>
            </div>
          </div>

          {loadingTechnical ? (
            <div className="technical-placeholder">Loading technical analysis...</div>
          ) : technicalError ? (
            <div className="technical-placeholder error">
              {technicalError}
              <p style={{ marginTop: '12px', fontSize: '14px', opacity: 0.7 }}>
                Technical analysis requires at least 50 data points. 
                {timeframe === 'MONTHLY' && ' For monthly analysis, you need at least 50 months of data.'}
                {timeframe === 'WEEKLY' && ' For weekly analysis, you need at least 50 weeks of data.'}
                {timeframe === 'DAILY' && ' For daily analysis, you need at least 50 days of data.'}
                {' '}Try selecting a longer date range or switch to a different timeframe.
              </p>
            </div>
          ) : technicalData ? (
            <div className="technical-indicators-grid">
              {/* Oscillators Section */}
              <div className="indicators-panel">
                <div className="indicators-summary">
                  <h3>Oscillators</h3>
                  <div className="gauge-container">
                    <div className="gauge-wrapper">
                      <svg className="gauge" viewBox="0 0 200 110" width="200" height="110">
                        <defs>
                          <linearGradient id="gauge-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                            <stop offset="0%" stopColor="#f87171" />
                            <stop offset="50%" stopColor="rgba(255,255,255,0.6)" />
                            <stop offset="100%" stopColor="#4ade80" />
                          </linearGradient>
                        </defs>
                        <path
                          d="M 20 90 A 80 80 0 0 1 180 90"
                          fill="none"
                          stroke="rgba(255,255,255,0.1)"
                          strokeWidth="12"
                        />
                        <path
                          d="M 20 90 A 80 80 0 0 1 180 90"
                          fill="none"
                          stroke={getSignalColor(technicalData.oscillatorSummary?.overallSignal)}
                          strokeWidth="12"
                          strokeLinecap="round"
                          strokeDasharray="251"
                          strokeDashoffset={251 * (1 - (calculateGaugeAngle(
                            technicalData.oscillatorSummary?.buyCount || 0,
                            technicalData.oscillatorSummary?.sellCount || 0,
                            technicalData.oscillatorSummary?.neutralCount || 0
                          ) / 180))}
                        />
                      </svg>
                      <div className="gauge-label">
                        <span style={{ color: getSignalColor(technicalData.oscillatorSummary?.overallSignal) }}>
                          {technicalData.oscillatorSummary?.overallSignal?.replace(/_/g, ' ') || 'Neutral'}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="summary-counts">
                    <span className="count sell">Sell {technicalData.oscillatorSummary?.sellCount || 0}</span>
                    <span className="count neutral">Neutral {technicalData.oscillatorSummary?.neutralCount || 0}</span>
                    <span className="count buy">Buy {technicalData.oscillatorSummary?.buyCount || 0}</span>
                  </div>
                </div>
                <div className="indicators-table">
                  <h4>Oscillators</h4>
                  <div className="table-scroll">
                    <table>
                      <thead>
                        <tr>
                          <th>Indicator</th>
                          <th>Value</th>
                          <th>Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {technicalData.oscillators?.map((osc, idx) => (
                          <tr key={idx}>
                            <td>{osc.displayName}</td>
                            <td>{osc.value?.toFixed(2) || '—'}</td>
                            <td>
                              <span className={`signal-badge ${getSignalClass(osc.signal)}`}>
                                {osc.signal || 'Neutral'}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>

              {/* Moving Averages Section */}
              <div className="indicators-panel">
                <div className="indicators-summary">
                  <h3>Moving Averages</h3>
                  <div className="gauge-container">
                    <div className="gauge-wrapper">
                      <svg className="gauge" viewBox="0 0 200 110" width="200" height="110">
                        <defs>
                          <linearGradient id="gauge-gradient-ma" x1="0%" y1="0%" x2="100%" y2="0%">
                            <stop offset="0%" stopColor="#f87171" />
                            <stop offset="50%" stopColor="rgba(255,255,255,0.6)" />
                            <stop offset="100%" stopColor="#4ade80" />
                          </linearGradient>
                        </defs>
                        <path
                          d="M 20 90 A 80 80 0 0 1 180 90"
                          fill="none"
                          stroke="rgba(255,255,255,0.1)"
                          strokeWidth="12"
                        />
                        <path
                          d="M 20 90 A 80 80 0 0 1 180 90"
                          fill="none"
                          stroke={getSignalColor(technicalData.movingAverageSummary?.overallSignal)}
                          strokeWidth="12"
                          strokeLinecap="round"
                          strokeDasharray="251"
                          strokeDashoffset={251 * (1 - (calculateGaugeAngle(
                            technicalData.movingAverageSummary?.buyCount || 0,
                            technicalData.movingAverageSummary?.sellCount || 0,
                            technicalData.movingAverageSummary?.neutralCount || 0
                          ) / 180))}
                        />
                      </svg>
                      <div className="gauge-label">
                        <span style={{ color: getSignalColor(technicalData.movingAverageSummary?.overallSignal) }}>
                          {technicalData.movingAverageSummary?.overallSignal?.replace(/_/g, ' ') || 'Neutral'}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="summary-counts">
                    <span className="count sell">Sell {technicalData.movingAverageSummary?.sellCount || 0}</span>
                    <span className="count neutral">Neutral {technicalData.movingAverageSummary?.neutralCount || 0}</span>
                    <span className="count buy">Buy {technicalData.movingAverageSummary?.buyCount || 0}</span>
                  </div>
                </div>
                <div className="indicators-table">
                  <h4>Moving Averages</h4>
                  <div className="table-scroll">
                    <table>
                      <thead>
                        <tr>
                          <th>Indicator</th>
                          <th>Value</th>
                          <th>Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {technicalData.movingAverages?.map((ma, idx) => (
                          <tr key={idx}>
                            <td>{ma.displayName}</td>
                            <td>{ma.value?.toFixed(2) || '—'}</td>
                            <td>
                              <span className={`signal-badge ${getSignalClass(ma.signal)}`}>
                                {ma.signal || 'Neutral'}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="technical-placeholder">No technical analysis data available.</div>
          )}
        </section>

        <section className="symbol-detail-table">
          <div className="section-header">
            <div>
              <h2>Daily breakdown</h2>
              <p>Detailed market data pulled directly from the database.</p>
            </div>
            <button className="download-button" onClick={handleDownloadCsv} disabled={!tableData.length}>
              Download CSV
            </button>
          </div>

          {loading ? (
            <div className="table-placeholder">Loading table...</div>
          ) : error ? (
            <div className="table-placeholder error">{error}</div>
          ) : tableData.length ? (
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Open</th>
                    <th>High</th>
                    <th>Low</th>
                    <th>Close</th>
                    <th>Volume</th>
                    <th>QuoteAssetVolume</th>
                    <th>Symbol</th>
                    <th>LastPrice_24h</th>
                    <th>Volume_24h</th>
                    <th>QuoteVolume_24h</th>
                    <th>High_24h</th>
                    <th>Low_24h</th>
                    <th>BaseAsset</th>
                    <th>QuoteAsset</th>
                    <th>SymbolUsed</th>
                  </tr>
                </thead>
                <tbody>
                  {tableData.map((entry) => (
                    <tr key={`${entry.symbol}-${entry.date}`}>
                      <td>{entry.date}</td>
                      <td>{entry.open ? `$${entry.open.toFixed(2)}` : '—'}</td>
                      <td>{entry.high ? `$${entry.high.toFixed(2)}` : '—'}</td>
                      <td>{entry.low ? `$${entry.low.toFixed(2)}` : '—'}</td>
                      <td>{entry.close ? `$${entry.close.toFixed(2)}` : '—'}</td>
                      <td>{(entry.volume ?? entry.volume_24h ?? 0).toLocaleString()}</td>
                      <td>{(entry.quoteAssetVolume ?? 0).toLocaleString()}</td>
                      <td>{entry.symbol || '—'}</td>
                      <td>{entry.lastPrice_24h ? `$${entry.lastPrice_24h.toFixed(2)}` : '—'}</td>
                      <td>{(entry.volume_24h ?? 0).toLocaleString()}</td>
                      <td>{(entry.quoteVolume_24h ?? 0).toLocaleString()}</td>
                      <td>{entry.high_24h ? `$${entry.high_24h.toFixed(2)}` : '—'}</td>
                      <td>{entry.low_24h ? `$${entry.low_24h.toFixed(2)}` : '—'}</td>
                      <td>{entry.baseAsset || '—'}</td>
                      <td>{entry.quoteAsset || '—'}</td>
                      <td>{entry.symbolUsed || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="table-placeholder">No rows available for the selected range.</div>
          )}
        </section>
      </div>
    </div>
  );
};

export default SymbolDetail;

