import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import './Homepage.css';

const Homepage = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [showResults, setShowResults] = useState(false);
  const [btcData, setBtcData] = useState([]);
  const [ethData, setEthData] = useState([]);
  const [xrpData, setXrpData] = useState([]);
  const [bnbData, setBnbData] = useState([]);
  const [solData, setSolData] = useState([]);
  const [dogeData, setDogeData] = useState([]);
  const [loading, setLoading] = useState(true);
  const searchRef = useRef(null);
  const navigate = useNavigate();

  // Crypto symbols for the grid
  const cryptoSymbols = [
    'BTCUSDT', 'USDCUSDT', 'ETHUSDT', 'ZECUSDT', 'BTCUSDC', 'SOLUSDT',
    'ETHUSDC', 'FDUSDUSDT', 'XRPUSDT', 'BNBUSDC', 'BNBUSDT', 'DOGEUSDT',
    'MMTUSDT', 'ASTERUSDT', 'SOLUSDC', 'TRXUSDT', 'XRPUSDC', 'STRKUSDT',
    'TNSRUSDT', 'SUIUSDT', 'BCHUSDT', 'FDUSDUSDC', 'ADAUSDT', 'DOGEUSDC',
    'USDEUSDT', 'LINKUSDT', 'PEPEUSDT', 'WLFIUSDT', 'METUSDT', 'AVAXUSDT',
    'LTCUSDT', 'ENAUSDT'
  ];

  // Fetch search results
  useEffect(() => {
    const fetchSearchResults = async () => {
      if (searchQuery.trim().length > 0) {
        try {
          const response = await fetch(`http://localhost:8080/api/search?query=${encodeURIComponent(searchQuery)}`);
          if (response.ok) {
            const data = await response.json();
            setSearchResults(data);
            setShowResults(true);
          }
        } catch (error) {
          console.error('Error fetching search results:', error);
        }
      } else {
        setSearchResults([]);
        setShowResults(false);
      }
    };

    const debounceTimer = setTimeout(fetchSearchResults, 300);
    return () => clearTimeout(debounceTimer);
  }, [searchQuery]);

  // Fetch chart data for all symbols
  useEffect(() => {
    const fetchChartData = async () => {
      setLoading(true);
      try {
        // Calculate date range for monthly data (last 12 months)
        const today = new Date();
        const oneYearAgo = new Date(today);
        oneYearAgo.setFullYear(today.getFullYear() - 1);
        const fromDate = oneYearAgo.toISOString().split('T')[0];
        const toDate = today.toISOString().split('T')[0];

        // Fetch data for all charts
        const [btcRes, ethRes, xrpRes, bnbRes, solRes, dogeRes] = await Promise.all([
          fetch(`http://localhost:8080/api/symbol/BTCUSDT?from=${fromDate}&to=${toDate}`),
          fetch(`http://localhost:8080/api/symbol/ETHUSDT?from=${fromDate}&to=${toDate}`),
          fetch(`http://localhost:8080/api/symbol/XRPUSDT?from=${fromDate}&to=${toDate}`),
          fetch(`http://localhost:8080/api/symbol/BNBUSDC?from=${fromDate}&to=${toDate}`),
          fetch(`http://localhost:8080/api/symbol/SOLUSDC?from=${fromDate}&to=${toDate}`),
          fetch(`http://localhost:8080/api/symbol/DOGEUSDT?from=${fromDate}&to=${toDate}`)
        ]);

        const [btc, eth, xrp, bnb, sol, doge] = await Promise.all([
          btcRes.json(),
          ethRes.json(),
          xrpRes.json(),
          bnbRes.json(),
          solRes.json(),
          dogeRes.json()
        ]);

        // Process data: group by month and get average close price per month
        const processData = (data) => {
          const grouped = {};
          data.forEach(item => {
            const date = new Date(item.date);
            const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
            if (!grouped[monthKey]) {
              grouped[monthKey] = { date: monthKey, close: item.close, count: 1 };
            } else {
              grouped[monthKey].close = (grouped[monthKey].close + item.close) / 2;
              grouped[monthKey].count++;
            }
          });
          return Object.values(grouped)
            .sort((a, b) => a.date.localeCompare(b.date))
            .map(item => {
              const [year, month] = item.date.split('-');
              const dateObj = new Date(year, parseInt(month) - 1);
              return {
                date: dateObj.toLocaleDateString('en-US', { month: 'short', year: 'numeric' }),
                close: item.close
              };
            });
        };

        setBtcData(processData(btc));
        setEthData(processData(eth));
        setXrpData(processData(xrp));
        setBnbData(processData(bnb));
        setSolData(processData(sol));
        setDogeData(processData(doge));
        setLoading(false);
      } catch (error) {
        console.error('Error fetching chart data:', error);
        setLoading(false);
      }
    };

    fetchChartData();
  }, []);

  // Handle click outside search to close results
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (searchRef.current && !searchRef.current.contains(event.target)) {
        setShowResults(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSymbolClick = (symbol) => {
    navigate(`/symbol/${symbol}`);
  };

  const handleSearchResultClick = (symbol) => {
    navigate(`/symbol/${symbol}`);
    setSearchQuery('');
    setShowResults(false);
  };

  // Get color for each crypto symbol
  const getCryptoColor = (symbol) => {
    const colorMap = {
      'BTCUSDT': '#f7931a',
      'ETHUSDT': '#627eea',
      'XRPUSDT': '#00d4ff',
      'BNBUSDT': '#f3ba2f',
      'BNBUSDC': '#f3ba2f',
      'SOLUSDT': '#14f195',
      'SOLUSDC': '#14f195',
      'DOGEUSDT': '#c2a633',
      'DOGEUSDC': '#c2a633',
      'ADAUSDT': '#0033ad',
      'TRXUSDT': '#ff0019',
      'LINKUSDT': '#375bd2',
      'AVAXUSDT': '#e84142',
      'LTCUSDT': '#bfbbbb',
      'BCHUSDT': '#0ac18e',
      'PEPEUSDT': '#3aaf4a',
      'SUIUSDT': '#5facfc',
      'STRKUSDT': '#ffd700',
      'TNSRUSDT': '#ff6b6b',
      'ENAUSDT': '#8b5cf6',
      'WLFIUSDT': '#00ff88',
      'METUSDT': '#ff0080',
      'MMTUSDT': '#00d9ff',
      'ASTERUSDT': '#ff6b35',
      'USDCUSDT': '#2775ca',
      'USDEUSDT': '#2775ca',
      'FDUSDUSDT': '#2775ca',
      'FDUSDUSDC': '#2775ca',
      'BTCUSDC': '#f7931a',
      'ETHUSDC': '#627eea',
      'XRPUSDC': '#00d4ff',
      'ZECUSDT': '#ecb244'
    };
    return colorMap[symbol] || '#4285F4';
  };

  // Prepare ticker items with colors
  const tickerItems = cryptoSymbols.map(symbol => ({
    symbol,
    color: getCryptoColor(symbol)
  }));

  // Duplicate items for seamless loop
  const duplicatedTickerItems = [...tickerItems, ...tickerItems];

  return (
    <div className="homepage">
      {/* Rotating Ticker */}
      <div className="rotating-ticker">
        <div className="ticker-content">
          {duplicatedTickerItems.map((item, index) => (
            <div
              key={index}
              className="ticker-item"
              style={{ '--crypto-color': item.color }}
              onClick={() => handleSymbolClick(item.symbol)}
            >
              <span className="ticker-badge">{item.symbol}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="homepage-container">
        {/* Search Bar */}
        <div className="search-section">
          <h1 className="search-section-title">Crypto Info</h1>
          <p className="search-section-subtitle">All you need at one place</p>
          <div className="search-container" ref={searchRef}>
            <input
              type="text"
              className="search-input"
              placeholder="Search crypto symbol..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onFocus={() => searchQuery.length > 0 && setShowResults(true)}
            />
          {showResults && searchResults.length > 0 && (
            <div className="search-results">
              {searchResults.map((symbol, index) => (
                <div
                  key={index}
                  className="search-result-item"
                  onClick={() => handleSearchResultClick(symbol)}
                >
                  {symbol}
                </div>
              ))}
            </div>
          )}
          </div>
        </div>

        {/* Crypto Grid */}
        <div className="crypto-grid">
          {cryptoSymbols.map((symbol, index) => (
            <div
              key={index}
              className="crypto-grid-item"
              onClick={() => handleSymbolClick(symbol)}
            >
              {symbol}
            </div>
          ))}
        </div>

        {/* Charts Section */}
        <div className="charts-section">
          {/* Full Width Charts - One below the other */}
          <div className="full-width-charts">
            <div className="chart-container full-width">
              <h3 className="chart-title">BTCUSDT - Monthly</h3>
              {loading ? (
                <div className="chart-loading">Loading...</div>
              ) : btcData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={btcData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.05)" />
                    <XAxis dataKey="date" stroke="rgba(255, 255, 255, 0.4)" />
                    <YAxis 
                      stroke="rgba(255, 255, 255, 0.4)"
                      tickFormatter={(value) => `$${value.toFixed(2)}`}
                    />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid rgba(255, 255, 255, 0.1)', color: '#fff' }}
                      formatter={(value) => [`$${value.toFixed(2)}`, 'Close']}
                    />
                    <Area
                      type="monotone"
                      dataKey="close"
                      stroke="#f7931a"
                      fill="#f7931a"
                      fillOpacity={0.2}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <div className="chart-no-data">No data available</div>
              )}
            </div>

            <div className="chart-container full-width">
              <h3 className="chart-title">ETHUSDT - Monthly</h3>
              {loading ? (
                <div className="chart-loading">Loading...</div>
              ) : ethData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={ethData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.05)" />
                    <XAxis dataKey="date" stroke="rgba(255, 255, 255, 0.4)" />
                    <YAxis 
                      stroke="rgba(255, 255, 255, 0.4)"
                      tickFormatter={(value) => `$${value.toFixed(2)}`}
                    />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid rgba(255, 255, 255, 0.1)', color: '#fff' }}
                      formatter={(value) => [`$${value.toFixed(2)}`, 'Close']}
                    />
                    <Area
                      type="monotone"
                      dataKey="close"
                      stroke="#627eea"
                      fill="#627eea"
                      fillOpacity={0.2}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <div className="chart-no-data">No data available</div>
              )}
            </div>
          </div>

          {/* Small Charts - 2x2 Grid */}
          <div className="small-charts-grid">
            <div className="chart-container small">
              <h4 className="chart-title-small">XRPUSDT</h4>
              {loading ? (
                <div className="chart-loading-small">Loading...</div>
              ) : xrpData.length > 0 ? (
                <ResponsiveContainer width="100%" height={150}>
                  <LineChart data={xrpData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.05)" />
                    <XAxis dataKey="date" stroke="rgba(255, 255, 255, 0.4)" />
                    <YAxis 
                      stroke="rgba(255, 255, 255, 0.4)"
                      tickFormatter={(value) => `$${value.toFixed(2)}`}
                    />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid rgba(255, 255, 255, 0.1)', color: '#fff' }}
                      formatter={(value) => [`$${value.toFixed(2)}`, 'Close']}
                    />
                    <Line
                      type="monotone"
                      dataKey="close"
                      stroke="#00d4ff"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="chart-no-data-small">No data</div>
              )}
            </div>

            <div className="chart-container small">
              <h4 className="chart-title-small">BNBUSDC</h4>
              {loading ? (
                <div className="chart-loading-small">Loading...</div>
              ) : bnbData.length > 0 ? (
                <ResponsiveContainer width="100%" height={150}>
                  <LineChart data={bnbData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.05)" />
                    <XAxis dataKey="date" stroke="rgba(255, 255, 255, 0.4)" />
                    <YAxis 
                      stroke="rgba(255, 255, 255, 0.4)"
                      tickFormatter={(value) => `$${value.toFixed(2)}`}
                    />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid rgba(255, 255, 255, 0.1)', color: '#fff' }}
                      formatter={(value) => [`$${value.toFixed(2)}`, 'Close']}
                    />
                    <Line
                      type="monotone"
                      dataKey="close"
                      stroke="#f3ba2f"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="chart-no-data-small">No data</div>
              )}
            </div>

            <div className="chart-container small">
              <h4 className="chart-title-small">SOLUSDC</h4>
              {loading ? (
                <div className="chart-loading-small">Loading...</div>
              ) : solData.length > 0 ? (
                <ResponsiveContainer width="100%" height={150}>
                  <LineChart data={solData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.05)" />
                    <XAxis dataKey="date" stroke="rgba(255, 255, 255, 0.4)" />
                    <YAxis 
                      stroke="rgba(255, 255, 255, 0.4)"
                      tickFormatter={(value) => `$${value.toFixed(2)}`}
                    />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid rgba(255, 255, 255, 0.1)', color: '#fff' }}
                      formatter={(value) => [`$${value.toFixed(2)}`, 'Close']}
                    />
                    <Line
                      type="monotone"
                      dataKey="close"
                      stroke="#14f195"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="chart-no-data-small">No data</div>
              )}
            </div>

            <div className="chart-container small">
              <h4 className="chart-title-small">DOGEUSDT</h4>
              {loading ? (
                <div className="chart-loading-small">Loading...</div>
              ) : dogeData.length > 0 ? (
                <ResponsiveContainer width="100%" height={150}>
                  <LineChart data={dogeData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.05)" />
                    <XAxis dataKey="date" stroke="rgba(255, 255, 255, 0.4)" />
                    <YAxis 
                      stroke="rgba(255, 255, 255, 0.4)"
                      tickFormatter={(value) => `$${value.toFixed(2)}`}
                    />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid rgba(255, 255, 255, 0.1)', color: '#fff' }}
                      formatter={(value) => [`$${value.toFixed(2)}`, 'Close']}
                    />
                    <Line
                      type="monotone"
                      dataKey="close"
                      stroke="#c2a633"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="chart-no-data-small">No data</div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Homepage;

