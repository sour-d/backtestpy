import React from 'react';
import { createChart, ColorType, AreaSeries, HistogramSeries } from 'lightweight-charts';
import { Box } from '@mui/material';

const ChartComponent = ({ data, title, seriesType, seriesOptions }) => {
  const chartContainerRef = React.useRef();
  const chartRef = React.useRef(null);
  const tooltipRef = React.useRef(null);

  React.useEffect(() => {
    if (!chartContainerRef.current) {
      return;
    }

    if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
    }

    const chartOptions = {
      layout: {
        background: { type: ColorType.Solid, color: '#1e1e1e' },
        textColor: '#e0e0e0',
      },
      grid: {
        vertLines: { color: '#333' },
        horzLines: { color: '#333' },
      },
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
      },
    };

    const chart = createChart(chartContainerRef.current, chartOptions);
    chartRef.current = chart;

    const series = chart.addSeries(seriesType, seriesOptions);

    series.setData(data);

    chart.timeScale().fitContent();

    const tooltip = tooltipRef.current;

    chart.subscribeCrosshairMove((param) => {
      if (
        param.point &&
        param.seriesData.get(series) &&
        param.seriesData.get(series).value !== undefined
      ) {
        const date = new Date(param.time * 1000).toLocaleDateString();
        const hoveredData = data.find(d => d.time === param.time);

        if (hoveredData) {
          const value = hoveredData.value !== undefined ? hoveredData.value.toFixed(2) : 'N/A';
          const equity = hoveredData.equity !== undefined ? hoveredData.equity.toFixed(2) : 'N/A';
          const absoluteDrawdown = hoveredData.absoluteDrawdown !== undefined ? hoveredData.absoluteDrawdown.toFixed(2) : 'N/A';

          tooltip.style.display = 'block';
          tooltip.style.left = param.point.x + 'px';
          tooltip.style.top = param.point.y + 'px';
          tooltip.innerHTML = `<div>${title}</div><div>Date: ${date}</div><div>Drawdown: ${value}%</div><div>Current Capital: ${equity}</div><div>Money Lost: ${absoluteDrawdown}</div>`;
        } else {
          tooltip.style.display = 'none';
        }
      } else {
        tooltip.style.display = 'none';
      }
    });

    return () => {
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }
    };
  }, [data, seriesType, seriesOptions, title]);

  return (
    <Box sx={{ position: 'relative', p: 2, borderRadius: '8px', backgroundColor: 'background.paper', marginBottom: '20px' }}>
      <h2 style={{ textAlign: 'center', color: 'text.primary', marginBottom: '10px' }}>{title}</h2>
      <div ref={chartContainerRef} style={{ width: '100%', height: '300px' }} />
      <Box
        ref={tooltipRef}
        sx={{
          position: 'absolute',
          display: 'none',
          p: '8px',
          background: 'rgba(0, 0, 0, 0.7)',
          color: '#fff',
          borderRadius: '4px',
          fontSize: '12px',
          pointerEvents: 'none',
          zIndex: 1000,
          transform: 'translate(-50%, -100%)', // Adjust to position above the cursor
        }}
      ></Box>
    </Box>
  );
};

const AdditionalCharts = ({ trades }) => {
  const initialCapital = 100000;
  let equity = initialCapital;
  let peakEquity = initialCapital;
  const equityCurve = [];
  const drawdownData = [];

  trades.forEach(trade => {
    equity += parseFloat(trade.net_profit_loss);
    if (equity > peakEquity) {
      peakEquity = equity;
    }
    const absoluteDrawdown = peakEquity - equity;
    const drawdownPct = (absoluteDrawdown / peakEquity) * 100;
    equityCurve.push({ time: new Date(trade.exit_date).getTime() / 1000, value: equity });
    drawdownData.push({
      time: new Date(trade.exit_date).getTime() / 1000,
      value: drawdownPct,
      equity: equity,
      absoluteDrawdown: absoluteDrawdown,
    });
  });

  const pnlData = trades.map(trade => ({
    time: new Date(trade.exit_date).getTime() / 1000,
    value: parseFloat(trade.net_profit_loss),
    color: parseFloat(trade.net_profit_loss) >= 0 ? 'rgba(38, 166, 154, 0.5)' : 'rgba(239, 83, 80, 0.5)',
  }));

  return (
    <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
      <ChartComponent 
        data={drawdownData} 
        title="Drawdown (%)" 
        seriesType={AreaSeries} 
        seriesOptions={{
          lineColor: '#FF0000',
          topColor: 'rgba(255, 0, 0, 0.4)',
          bottomColor: 'rgba(255, 0, 0, 0)',
        }}
      />
      <ChartComponent 
        data={pnlData} 
        title="Profit/Loss" 
        seriesType={HistogramSeries} 
        seriesOptions={{
          color: '#26a69a',
        }}
      />
    </Box>
  );
};

export default AdditionalCharts;