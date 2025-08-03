import React from 'react';
import { Card, CardContent, Typography, Grid, Box } from '@mui/material';

const SummaryGroup = ({ title, data, valueFormatter = (value) => value }) => (
  <Box sx={{ marginBottom: '20px' }}>
    <Typography variant="h6" gutterBottom sx={{ color: '#e0e0e0', borderBottom: '1px solid #333', paddingBottom: '5px', marginBottom: '10px' }}>
      {title}
    </Typography>
    <Grid container spacing={2}>
      {Object.entries(data).map(([key, value]) => (
        <Grid item xs={12} sm={6} md={4} key={key}>
          <Card sx={{ backgroundColor: '#1e1e1e', color: '#e0e0e0', height: '100%' }}>
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary" sx={{ color: '#aaa' }}>
                {key.replace(/_/g, ' ')}
              </Typography>
              <Typography variant="h6" component="div" sx={{ fontWeight: 'bold' }}>
                {valueFormatter(value, key)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  </Box>
);

const SummarySection = ({ summary }) => {
  if (!summary) return null;

  const formatCurrency = (value) => `$${value.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
  const formatPercentage = (value) => `${value.toLocaleString(undefined, { maximumFractionDigits: 2 })}%`;
  const formatNumber = (value) => value.toLocaleString(undefined, { maximumFractionDigits: 2 });

  const overallPerformance = {
    initial_capital: summary.initial_capital,
    final_capital: summary.final_capital,
    net_profit: summary.net_profit,
    gross_profit: summary.gross_profit,
    total_fees_paid: summary.total_fees_paid,
    total_return_pct: ((summary.final_capital / summary.initial_capital - 1) * 100),
  };

  const tradeStatistics = {
    total_trades: summary.total_trades,
    winning_trades: summary.winning_trades,
    losing_trades: summary.losing_trades,
    breakeven_trades: summary.breakeven_trades,
    win_rate: summary.win_rate,
  };

  const profitLossMetrics = {
    avg_trade: summary.avg_trade,
    avg_profit_per_win: summary.avg_profit_per_win,
    avg_loss_per_loss: summary.avg_loss_per_loss,
    max_win: summary.max_win,
    max_loss: summary.max_loss,
    best_trade: summary.best_trade,
    worst_trade: summary.worst_trade,
  };

  const riskDrawdown = {
    max_drawdown: summary.max_drawdown,
    max_drawdown_pct: summary.max_drawdown_pct,
    sharpe_ratio: summary.sharpe_ratio,
    profit_factor: summary.profit_factor,
    expectancy: summary.expectancy,
  };

  const longShortAnalysis = {
    total_long_trades: summary.total_long_trades,
    total_short_trades: summary.total_short_trades,
    long_win_rate: summary.long_win_rate,
    short_win_rate: summary.short_win_rate,
  };

  const consecutiveTrades = {
    max_consecutive_wins: summary.max_consecutive_wins,
    max_consecutive_losses: summary.max_consecutive_losses,
    current_streak: `${summary.current_streak} ${summary.current_streak_type}`,
  };

  const durationAnalysis = {
    avg_trade_duration: summary.avg_trade_duration,
  };

  return (
    <Box sx={{ p: 2, borderRadius: '8px', backgroundColor: 'background.paper', marginBottom: '20px' }}>
      <Typography variant="h5" component="h2" gutterBottom sx={{ marginBottom: '20px' }}>
        Backtest Summary
      </Typography>

      <SummaryGroup 
        title="Overall Performance" 
        data={overallPerformance} 
        valueFormatter={(value, key) => {
          if (key.includes('capital') || key.includes('profit') || key.includes('fees')) return formatCurrency(value);
          if (key.includes('pct')) return formatPercentage(value);
          return formatNumber(value);
        }}
      />
      <SummaryGroup 
        title="Trade Statistics" 
        data={tradeStatistics} 
        valueFormatter={(value, key) => {
          if (key.includes('rate')) return formatPercentage(value);
          return formatNumber(value);
        }}
      />
      <SummaryGroup 
        title="Profit & Loss Metrics" 
        data={profitLossMetrics} 
        valueFormatter={(value, key) => {
          if (key.includes('trade') || key.includes('win') || key.includes('loss')) return formatCurrency(value);
          return formatNumber(value);
        }}
      />
      <SummaryGroup 
        title="Risk & Drawdown" 
        data={riskDrawdown} 
        valueFormatter={(value, key) => {
          if (key.includes('drawdown') && !key.includes('pct')) return formatCurrency(value);
          if (key.includes('pct')) return formatPercentage(value);
          return formatNumber(value);
        }}
      />
      <SummaryGroup 
        title="Long/Short Analysis" 
        data={longShortAnalysis} 
        valueFormatter={(value, key) => {
          if (key.includes('rate')) return formatPercentage(value);
          return formatNumber(value);
        }}
      />
      <SummaryGroup 
        title="Consecutive Trades" 
        data={consecutiveTrades} 
        valueFormatter={formatNumber}
      />
      {summary.avg_trade_duration > 0 && (
        <SummaryGroup 
          title="Duration Analysis" 
          data={durationAnalysis} 
          valueFormatter={(value) => {
            if (value < 24) return `${value.toLocaleString(undefined, { maximumFractionDigits: 1 })} hours`;
            return `${(value / 24).toLocaleString(undefined, { maximumFractionDigits: 1 })} days`;
          }}
        />
      )}
    </Box>
  );
};

export default SummarySection;
