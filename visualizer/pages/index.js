import React, { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import { Container, Box } from '@mui/material';

import Header from '../components/Header';
import SummarySection from '../components/SummarySection';
import TradesTable from '../components/TradesTable';
import AdditionalCharts from '../components/AdditionalCharts';

const Chart = dynamic(() => import('../components/Chart'), {
  ssr: false,
  loading: () => (
    <Box
      sx={{
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
    </Box>
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

        if (data.trades && data.trades.length > 0) {
          setTradeData(data.trades);
        }
      })
      .catch(err => {
        console.error('Error loading result:', err);
      });
  };

  return (
    <Container maxWidth={false} sx={{ padding: '20px' }}>
      <Header results={results} selectedResult={selectedResult} onSelectResult={loadResult} />

      {summary && <SummarySection summary={summary} />}

      {chartData.length > 0 && (
        <Box sx={{ marginBottom: '20px' }}>
          <h2 style={{ marginBottom: '15px', fontSize: '1.8rem' }}>
            Price Chart
          </h2>
          <Chart data={chartData} trades={tradeData} title={selectedResult ? `${selectedResult} Price Chart` : "Price Chart"} />
        </Box>
      )}

      {tradeData.length > 0 && <AdditionalCharts trades={tradeData} />}

      {tradeData.length > 0 && <TradesTable tradeData={tradeData} />}
    </Container>
  );
};

export default Home;