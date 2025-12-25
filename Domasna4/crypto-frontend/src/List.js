import { useState, useEffect, useRef } from 'react';
import './App.css';

const List = () => {
  const [cryptos, setCryptos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingProgress, setLoadingProgress] = useState({ current: 0, total: 0 });
  const [scrollTop, setScrollTop] = useState(0);
  const scrollContainerRef = useRef(null);
  
  // Virtual scrolling constants
  const ITEM_HEIGHT = 30; // Approximate height of each item in pixels
  const CONTAINER_HEIGHT = 600; // Height of visible container
  const OVERSCAN = 10; // Number of items to render outside visible area

  useEffect(() => {
    const fetchAllCryptos = async () => {
      try {
        setLoading(true);
        const allData = [];
        const pageSize = 10000; // Backend limit per request
        let page = 0;
        let hasMore = true;
        let totalFetched = 0;
        // Fetch ALL records - no limit with virtual scrolling
        // First, fetch the first page to see how many records we have
        const firstResponse = await fetch(`http://localhost:8080/api?page=0&size=${pageSize}`);
        if (!firstResponse.ok) {
          throw new Error(`HTTP error! status: ${firstResponse.status}`);
        }
        const firstData = await firstResponse.json();
        allData.push(...firstData);
        totalFetched += firstData.length;

        // Continue fetching all pages
        if (firstData.length === pageSize) {
          setLoadingProgress({ current: totalFetched, total: 'calculating...' });
          
          page = 1;
          while (hasMore) {
            // Add a small delay to prevent overwhelming the browser/network
            await new Promise(resolve => setTimeout(resolve, 50));
            
            const response = await fetch(`http://localhost:8080/api?page=${page}&size=${pageSize}`);
            if (!response.ok) {
              throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            
            if (data.length === 0) {
              hasMore = false;
            } else {
              allData.push(...data);
              totalFetched += data.length;
              setLoadingProgress({ current: totalFetched, total: totalFetched });
              
              // If we got less than pageSize, we've reached the end
              if (data.length < pageSize) {
                hasMore = false;
              } else {
                page++;
              }
            }
          }
        }

        setCryptos(allData);
        setLoadingProgress({ current: allData.length, total: allData.length });
        setLoading(false);
      } catch (error) {
        console.error('Error fetching cryptocurrency data:', error);
        setLoading(false);
      }
    };

    fetchAllCryptos();
  }, []);

  // Display all cryptos
  const displayCryptos = cryptos;

  // Virtual scrolling calculations
  const totalItems = displayCryptos.length;
  const totalHeight = totalItems * ITEM_HEIGHT;
  const startIndex = Math.max(0, Math.floor(scrollTop / ITEM_HEIGHT) - OVERSCAN);
  const endIndex = Math.min(
    totalItems - 1,
    Math.ceil((scrollTop + CONTAINER_HEIGHT) / ITEM_HEIGHT) + OVERSCAN
  );
  const visibleItems = displayCryptos.slice(startIndex, endIndex + 1);
  const offsetY = startIndex * ITEM_HEIGHT;

  // Handle scroll
  const handleScroll = (e) => {
    setScrollTop(e.target.scrollTop);
  };

  if (loading) {
    return (
      <div className="App">
        <header className="App-header">
          <h1>CryptoInfo</h1>
          <div style={{ marginTop: '20px' }}>
            <p>Loading cryptocurrency data...</p>
            <p>Fetched: {loadingProgress.current} records</p>
            {loadingProgress.total !== 'calculating...' && (
              <p>Total: {loadingProgress.total} records</p>
            )}
          </div>
        </header>
      </div>
    );
  }

  return (
    <div className="App">
      <header className="App-header">
        <h1>CryptoInfo</h1>
        <div style={{ marginBottom: '20px' }}>
          <p style={{ marginTop: '10px' }}>
            Showing {cryptos.length} total records (using virtual scrolling)
            <span style={{ color: 'green', marginLeft: '10px' }}>
              ✓ Virtual scrolling enabled - all records loaded
            </span>
          </p>
        </div>
        <div 
          ref={scrollContainerRef}
          className="crypto-list" 
          style={{ 
            height: `${CONTAINER_HEIGHT}px`, 
            overflowY: 'auto',
            position: 'relative'
          }}
          onScroll={handleScroll}
        >
          {displayCryptos.length === 0 ? (
            <p>No records found.</p>
          ) : (
            <div style={{ height: `${totalHeight}px`, position: 'relative' }}>
              {/* Spacer for items above visible area */}
              {startIndex > 0 && <div style={{ height: `${offsetY}px` }} />}
              
              {/* Only render visible items */}
              {visibleItems.map((crypto, index) => {
                const symbol = crypto.symbolUsed || crypto.symbol;
                const name = crypto.baseAsset || symbol;
                const price = crypto.lastPrice_24h || crypto.close;
                const priceFormatted = price ? price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : 'N/A';
                const dateFormatted = crypto.date ? new Date(crypto.date).toLocaleDateString() : 'N/A';
                
                return (
                  <div 
                    key={crypto.id} 
                    className="crypto-item"
                    style={{ 
                      height: `${ITEM_HEIGHT}px`,
                      display: 'flex',
                      alignItems: 'center',
                      padding: '5px 0'
                    }}
                  >
                    {name} ({symbol}): ${priceFormatted} - {dateFormatted}
                  </div>
                );
              })}
              
              {/* Spacer for items below visible area */}
              {endIndex < totalItems - 1 && (
                <div style={{ height: `${totalHeight - (endIndex + 1) * ITEM_HEIGHT}px` }} />
              )}
            </div>
          )}
        </div>
      </header>
    </div>
  );
}

export default List;

