import React, { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';

// Dynamic import to avoid SSR issues
const Chart = dynamic(() => import('../components/Chart'), {
  ssr: false,
  loading: () => (
    <div
      style={{
        width: '100%',
        height: '500px',
        backgroundColor: '#1e1e1e',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        borderRadius: '8px',
      }}
    >
      Loading chart...
    </div>
  ),
});

const Home = () => {
  const [results, setResults] = useState([]);
  const [selectedResult, setSelectedResult] = useState(null);
  const [summary, setSummary] = useState(null);
  const [chartData, setChartData] = useState([]);
  const [tradeData, setTradeData] = useState([]);

  useEffect(() => {
    fetch('/api/results')
      .then(res => res.json())
      .then(data => {
        setResults(data);
        if (data.length > 0) {
          loadResult(data[0]);
        }
      });
  }, []);

  const loadResult = (resultName) => {
    fetch(`/api/results?name=${resultName}`)
      .then(res => res.json())
      .then(data => {
        setSelectedResult(resultName);
        setSummary(data.summary);

        // Format chart data
        if (data.rawData && data.rawData.length > 0) {
          const formattedChartData = data.rawData.map(d => ({
            date: d.timestamp ? new Date(parseInt(d.timestamp)).toISOString().split('T')[0] : (d.Date || d.date),
            open: parseFloat(d.open),
            high: parseFloat(d.high),
            low: parseFloat(d.low),
            close: parseFloat(d.close),
            volume: parseFloat(d.volume),
          })).filter(d => !isNaN(d.open) && !isNaN(d.high) && !isNaN(d.low) && !isNaN(d.close) && !isNaN(d.volume) && typeof (d.timestamp ? new Date(parseInt(d.timestamp)).toISOString().split('T')[0] : (d.Date || d.date)) === 'string');
          setChartData(formattedChartData);
        }

        // Format trade data
        if (data.trades && data.trades.length > 0) {
          setTradeData(data.trades);
        }
      })
      .catch(err => {
        console.error('Error loading result:', err);
      });
  };

  return (
    <div
      style={{
        fontFamily:
          '-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Oxygen, Ubuntu, Cantarell, Open Sans, Helvetica Neue, sans-serif',
        backgroundColor: '#121212',
        color: '#e0e0e0',
        minHeight: '100vh',
        padding: '20px',
      }}
    >
      {/* Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '20px',
        }}
      >
        <h1 style={{ fontSize: '2.2rem' }}>Backtest Visualizer</h1>
        <select
          onChange={(e) => loadResult(e.target.value)}
          value={selectedResult || ''}
          style={{
            padding: '10px',
            borderRadius: '5px',
            border: '1px solid #333',
            backgroundColor: '#2c2c2c',
            color: '#e0e0e0',
            fontSize: '1rem',
          }}
        >
          {results.map((result) => (
            <option key={result} value={result}>
              {result}
            </option>
          ))}
        </select>
      </div>

      {/* Chart Section */}
      {chartData.length > 0 && (
        <div
          style={{
            backgroundColor: '#1e1e1e',
            padding: '20px',
            borderRadius: '8px',
            marginBottom: '20px',
          }}
        >
          <h2 style={{ marginBottom: '15px', fontSize: '1.8rem' }}>
            Price Chart
          </h2>
          <Chart data={chartData} trades={tradeData} title={selectedResult ? `${selectedResult} Price Chart` : "Price Chart"} />
        </div>
      )}

      {/* Trades Table Section */}
      {tradeData.length > 0 && (
        <div
          style={{
            backgroundColor: '#1e1e1e',
            padding: '20px',
            borderRadius: '8px',
            marginBottom: '20px',
          }}
        >
          <h2 style={{ marginBottom: '15px', fontSize: '1.8rem' }}>
            Trade History ({tradeData.length} trades)
          </h2>
          <div style={{ overflowX: 'auto' }}>
            <table
              style={{
                width: '100%',
                borderCollapse: 'collapse',
                backgroundColor: '#2c2c2c',
                borderRadius: '6px',
                overflow: 'hidden',
              }}
            >
              <thead>
                <tr style={{ backgroundColor: '#333' }}>
                  <th style={{ padding: '12px', textAlign: 'left', fontWeight: 'bold' }}>Type</th>
                  <th style={{ padding: '12px', textAlign: 'left', fontWeight: 'bold' }}>Entry Date</th>
                  <th style={{ padding: '12px', textAlign: 'left', fontWeight: 'bold' }}>Exit Date</th>
                  <th style={{ padding: '12px', textAlign: 'right', fontWeight: 'bold' }}>Entry Price</th>
                  <th style={{ padding: '12px', textAlign: 'right', fontWeight: 'bold' }}>Exit Price</th>
                  <th style={{ padding: '12px', textAlign: 'right', fontWeight: 'bold' }}>Quantity</th>
                  <th style={{ padding: '12px', textAlign: 'right', fontWeight: 'bold' }}>P&L</th>
                  <th style={{ padding: '12px', textAlign: 'right', fontWeight: 'bold' }}>P&L %</th>
                  <th style={{ padding: '12px', textAlign: 'left', fontWeight: 'bold' }}>Exit Reason</th>
                </tr>
              </thead>
              <tbody>
                {tradeData.map((trade, index) => (
                  <tr
                    key={index}
                    style={{
                      borderBottom: '1px solid #444',
                      '&:hover': { backgroundColor: '#333' },
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#333')}
                    onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
                  >
                    <td style={{ padding: '12px' }}>
                      <span
                        style={{
                          padding: '4px 8px',
                          borderRadius: '4px',
                          fontSize: '0.85rem',
                          fontWeight: 'bold',
                          backgroundColor: trade.type === 'buy' ? '#26a69a' : '#ef5350',
                          color: 'white',
                        }}
                      >
                        {trade.type?.toUpperCase()}
                      </span>
                    </td>
                    <td style={{ padding: '12px', fontSize: '0.9rem' }}>
                      {new Date(trade.entry_date).toLocaleDateString('en-US', {
                        day: 'numeric',
                        month: 'short',
                        year: 'numeric'
                      })}
                    </td>
                    <td style={{ padding: '12px', fontSize: '0.9rem' }}>
                      {new Date(trade.exit_date).toLocaleDateString('en-US', {
                        day: 'numeric',
                        month: 'short',
                        year: 'numeric'
                      })}
                    </td>
                    <td style={{ padding: '12px', textAlign: 'right', fontFamily: 'monospace' }}>
                      ${parseFloat(trade.entry_price).toFixed(2)}
                    </td>
                    <td style={{ padding: '12px', textAlign: 'right', fontFamily: 'monospace' }}>
                      ${parseFloat(trade.exit_price).toFixed(2)}
                    </td>
                    <td style={{ padding: '12px', textAlign: 'right', fontFamily: 'monospace' }}>
                      {parseFloat(trade.quantity).toFixed(4)}
                    </td>
                    <td
                      style={{
                        padding: '12px',
                        textAlign: 'right',
                        fontFamily: 'monospace',
                        fontWeight: 'bold',
                        color: parseFloat(trade.net_profit_loss) >= 0 ? '#26a69a' : '#ef5350',
                      }}
                    >
                      ${parseFloat(trade.net_profit_loss).toFixed(2)}
                    </td>
                    <td
                      style={{
                        padding: '12px',
                        textAlign: 'right',
                        fontFamily: 'monospace',
                        fontWeight: 'bold',
                        color: parseFloat(trade.net_profit_loss_pct) >= 0 ? '#26a69a' : '#ef5350',
                      }}
                    >
                      {parseFloat(trade.net_profit_loss_pct).toFixed(2)}%
                    </td>
                    <td style={{ padding: '12px', fontSize: '0.85rem', color: '#ccc' }}>
                      {trade.exit_reason}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Summary Section */}
      {summary && (
        <div
          style={{
            backgroundColor: '#1e1e1e',
            padding: '20px',
            borderRadius: '8px',
            marginTop: '20px',
          }}
        >
          <h2 style={{ marginBottom: '15px', fontSize: '1.8rem' }}>
            Backtest Summary
          </h2>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '15px',
            }}
          >
            {Object.entries(summary).map(([key, value]) => {
              if (typeof value !== 'object') {
                return (
                  <div
                    key={key}
                    style={{
                      backgroundColor: '#2c2c2c',
                      padding: '15px',
                      borderRadius: '6px',
                      transition: 'transform 0.2s ease',
                      cursor: 'default',
                    }}
                    onMouseEnter={(e) =>
                      (e.currentTarget.style.transform = 'scale(1.02)')
                    }
                    onMouseLeave={(e) =>
                      (e.currentTarget.style.transform = 'scale(1)')
                    }
                  >
                    <div
                      style={{
                        fontWeight: 'bold',
                        marginBottom: '8px',
                        color: '#aaa',
                        fontSize: '0.9rem',
                        textTransform: 'capitalize',
                      }}
                    >
                      {key.replace(/_/g, ' ')}
                    </div>
                    <div
                      style={{
                        fontSize: '1.2em',
                        fontWeight: '500',
                        color: '#fff',
                      }}
                    >
                      {typeof value === 'number'
                        ? value.toLocaleString(undefined, {
                          maximumFractionDigits: 2,
                        })
                        : value}
                    </div>
                  </div>
                );
              }
              return null;
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default Home;
