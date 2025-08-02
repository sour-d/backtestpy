import React, { useEffect, useRef, useState } from 'react';
import { createChart, ColorType, CandlestickSeries, HistogramSeries, createSeriesMarkers } from 'lightweight-charts';

const ChartComponent = ({ data, trades = [], title = "Candlestick Chart" }) => {
  const chartContainerRef = useRef();
  const chartRef = useRef(null);
  const candlestickSeriesRef = useRef(null);
  const volumeSeriesRef = useRef(null);

  useEffect(() => {
    if (!chartContainerRef.current) {
      return;
    }

    // Only create the chart if it hasn't been created yet
    if (chartRef.current) {
      return;
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

    const candlestickSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    });
    candlestickSeriesRef.current = candlestickSeries;

    const volumeSeries = chart.addSeries(HistogramSeries, {
      color: '#26a69a',
      priceFormat: {
        type: 'volume',
      },
      overlay: true,
      scaleMargins: {
        top: 0.8,
        bottom: 0,
      },
      priceScaleId: '', // Assign to a new, invisible price scale
    });
    volumeSeriesRef.current = volumeSeries;

    // Configure the new price scale for volume
    chart.priceScale('').applyOptions({
      scaleMargins: {
        top: 0.7,
        bottom: 0,
      },
      borderVisible: false,
      visible: false,
    });
    volumeSeriesRef.current = volumeSeries;

    return () => {
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (!chartRef.current || !candlestickSeriesRef.current || !volumeSeriesRef.current || !data || data.length === 0) {
      return;
    }

    const formattedCandleData = data.map(d => ({
      time: new Date(d.date).getTime() / 1000, // Convert to Unix timestamp for lightweight-charts
      open: parseFloat(d.open),
      high: parseFloat(d.high),
      low: parseFloat(d.low),
      close: parseFloat(d.close),
    }));

    const formattedVolumeData = data.map(d => ({
      time: new Date(d.date).getTime() / 1000, // Convert to Unix timestamp
      value: parseFloat(d.volume),
      color: d.close > d.open ? 'rgba(38, 166, 154, 0.5)' : 'rgba(239, 83, 80, 0.5)',
    }));

    candlestickSeriesRef.current.setData(formattedCandleData);
    volumeSeriesRef.current.setData(formattedVolumeData);

    // Add markers for trades
    const markers = [];
    const candleTimes = new Set(formattedCandleData.map(d => d.time));

    const findClosestCandleTime = (targetTime) => {
      // Find the closest available candle time
      // This is a simplified approach and might need refinement for edge cases
      const sortedCandleTimes = Array.from(candleTimes).sort((a, b) => a - b);
      let closestTime = null;
      let minDiff = Infinity;

      for (const time of sortedCandleTimes) {
        const diff = Math.abs(time - targetTime);
        if (diff < minDiff) {
          minDiff = diff;
          closestTime = time;
        }
      }
      return closestTime;
    };

    trades.forEach(trade => {
      // Entry marker
      const entryDate = new Date(trade.entry_date);
      const entryTime = entryDate.getTime() / 1000;
      const snappedEntryTime = findClosestCandleTime(entryTime);

      if (snappedEntryTime) {
        markers.push({
          time: snappedEntryTime,
          position: trade.type.toUpperCase() === 'BUY' ? 'belowBar' : 'aboveBar',
          color: trade.type.toUpperCase() === 'BUY' ? '#00FF00' : '#FF0000',
          shape: trade.type.toUpperCase() === 'BUY' ? 'arrowUp' : 'arrowDown',
          text: trade.type.toUpperCase() === 'BUY' ? 'L' : 'S',
        });
      }

      // Exit marker
      const exitDate = new Date(trade.exit_date);
      const exitTime = exitDate.getTime() / 1000;
      const snappedExitTime = findClosestCandleTime(exitTime);

      if (snappedExitTime) {
        markers.push({
          time: snappedExitTime,
          position: trade.type.toUpperCase() === 'BUY' ? 'aboveBar' : 'belowBar',
          color: trade.type.toUpperCase() === 'BUY' ? '#FF0000' : '#00FF00',
          shape: trade.type === 'BUY' ? 'arrowDown' : 'arrowUp',
          text: 'E',
        });
      }
    });
    createSeriesMarkers(candlestickSeriesRef.current, markers);

    chartRef.current.timeScale().fitContent();
    // Ensure all markers are visible by setting the visible range
    if (data.length > 0) {
      const firstTime = new Date(data[0].date).getTime() / 1000;
      const lastTime = new Date(data[data.length - 1].date).getTime() / 1000;

      chartRef.current.timeScale().setVisibleRange({
        from: firstTime,
        to: lastTime,
      });
    }
  }, [data, trades]);

  return (
    <div style={{ backgroundColor: '#1e1e1e', padding: '20px', borderRadius: '8px' }}>
      <h2 style={{ textAlign: 'center', color: '#e0e0e0', marginBottom: '10px' }}>{title}</h2>
      <div ref={chartContainerRef} style={{ width: '100%', height: '500px' }} />
    </div>
  );
};

export default ChartComponent;
