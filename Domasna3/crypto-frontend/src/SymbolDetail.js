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

  useEffect(() => {
    setFormRange(defaultRange);
    fetchSymbolData(defaultRange.from, defaultRange.to);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedSymbol, defaultRange.from, defaultRange.to]);

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

