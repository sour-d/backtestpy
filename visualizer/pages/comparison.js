import React, { useState, useEffect } from 'react';
import { Container, Typography, Box, CircularProgress, Paper, Grid } from '@mui/material';
import Header from '../components/Header';
import ComparisonTable from '../components/ComparisonTable';

const ComparisonPage = () => {
  const [summaries, setSummaries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchAllSummaries = async () => {
      try {
        const savedMode = localStorage.getItem('visualizer_mode') || 'backtest';
        const response = await fetch(`/api/results?allSummaries=true&mode=${savedMode}`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setSummaries(data);
      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    };

    fetchAllSummaries();
  }, []);

  const calculateAggregatedSummary = () => {
    if (summaries.length === 0) return null;

    const totalRuns = summaries.length;
    const initialCapitalPerRun = summaries[0].initial_capital; // Assuming initial capital is same for all
    const aggregatedInitialCapital = initialCapitalPerRun * totalRuns;

    const aggregated = summaries.reduce((acc, summary) => {
      acc.net_profit += summary.net_profit || 0;
      acc.total_fees_paid += summary.total_fees_paid || 0;
      acc.winning_trades += summary.winning_trades || 0;
      acc.losing_trades += summary.losing_trades || 0;
      acc.breakeven_trades += summary.breakeven_trades || 0;
      acc.total_trades += summary.total_trades || 0;
      acc.avg_profit_per_win += summary.avg_profit_per_win || 0;
      acc.avg_loss_per_loss += summary.avg_loss_per_loss || 0;
      acc.max_win += summary.max_win || 0;
      acc.max_loss += summary.max_loss || 0;
      acc.avg_trade += summary.avg_trade || 0;
      acc.max_drawdown_pct += summary.max_drawdown_pct || 0;
      acc.sharpe_ratio += summary.sharpe_ratio || 0;
      acc.profit_factor += summary.profit_factor || 0;
      acc.expectancy += summary.expectancy || 0;
      acc.total_long_trades += summary.total_long_trades || 0;
      acc.total_short_trades += summary.total_short_trades || 0;
      acc.long_win_rate += summary.long_win_rate || 0;
      acc.short_win_rate += summary.short_win_rate || 0;
      acc.max_consecutive_wins += summary.max_consecutive_wins || 0;
      acc.max_consecutive_losses += summary.max_consecutive_losses || 0;
      acc.avg_trade_duration += summary.avg_trade_duration || 0;
      return acc;
    }, {
      net_profit: 0,
      total_fees_paid: 0,
      winning_trades: 0,
      losing_trades: 0,
      breakeven_trades: 0,
      total_trades: 0,
      avg_profit_per_win: 0,
      avg_loss_per_loss: 0,
      max_win: 0,
      max_loss: 0,
      avg_trade: 0,
      max_drawdown_pct: 0,
      sharpe_ratio: 0,
      profit_factor: 0,
      expectancy: 0,
      total_long_trades: 0,
      total_short_trades: 0,
      long_win_rate: 0,
      short_win_rate: 0,
      max_consecutive_wins: 0,
      max_consecutive_losses: 0,
      avg_trade_duration: 0,
    });

    const finalCapital = aggregatedInitialCapital + aggregated.net_profit;
    const totalReturnPct = (aggregated.net_profit / aggregatedInitialCapital) * 100;

    const winRate = (aggregated.winning_trades / aggregated.total_trades) * 100 || 0;
    const longWinRate = (aggregated.long_win_rate / totalRuns) || 0;
    const shortWinRate = (aggregated.short_win_rate / totalRuns) || 0;

    return {
      total_runs: totalRuns,
      initial_capital: aggregatedInitialCapital,
      final_capital: finalCapital,
      net_profit: aggregated.net_profit,
      total_fees_paid: aggregated.total_fees_paid,
      total_return_pct: totalReturnPct,
      total_trades: aggregated.total_trades,
      winning_trades: aggregated.winning_trades,
      losing_trades: aggregated.losing_trades,
      breakeven_trades: aggregated.breakeven_trades,
      win_rate: winRate,
      avg_profit_per_win: aggregated.avg_profit_per_win / totalRuns,
      avg_loss_per_loss: aggregated.avg_loss_per_loss / totalRuns,
      max_win: aggregated.max_win / totalRuns,
      max_loss: aggregated.max_loss / totalRuns,
      avg_trade: aggregated.avg_trade / totalRuns,
      max_drawdown_pct: aggregated.max_drawdown_pct / totalRuns,
      sharpe_ratio: aggregated.sharpe_ratio / totalRuns,
      profit_factor: aggregated.profit_factor / totalRuns,
      expectancy: aggregated.expectancy / totalRuns,
      total_long_trades: aggregated.total_long_trades,
      total_short_trades: aggregated.total_short_trades,
      long_win_rate: longWinRate,
      short_win_rate: shortWinRate,
      max_consecutive_wins: aggregated.max_consecutive_wins / totalRuns,
      max_consecutive_losses: aggregated.max_consecutive_losses / totalRuns,
      avg_trade_duration: aggregated.avg_trade_duration / totalRuns,
    };
  };

  const aggregatedSummary = calculateAggregatedSummary();

  const formatValue = (value, key) => {
    if (typeof value !== 'number') return value;

    // Currency values
    if (['initial_capital', 'final_capital', 'net_profit', 'total_fees_paid', 'avg_profit_per_win', 'avg_loss_per_loss', 'max_win', 'max_loss', 'avg_trade', 'expectancy'].includes(key)) {
      return `${value.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
    }
    // Percentage values
    if (['total_return_pct', 'win_rate', 'max_drawdown_pct', 'long_win_rate', 'short_win_rate'].includes(key)) {
      return `${value.toLocaleString(undefined, { maximumFractionDigits: 2 })}%`;
    }
    // Durations
    if (key === 'avg_trade_duration') {
      if (value < 24) return `${value.toLocaleString(undefined, { maximumFractionDigits: 1 })} hours`;
      return `${(value / 24).toLocaleString(undefined, { maximumFractionDigits: 1 })} days`;
    }
    // Unitless values (counts, ratios)
    return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
  };

  return (
    <Container maxWidth="lg" sx={{ padding: '20px' }}>
      <Header results={[]} selectedResult={null} onSelectResult={() => {}} showComparisonLink={false} /> {/* Header without select for this page */}
      <Box sx={{ my: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom sx={{ color: 'text.primary' }}>
          Backtest Comparison
        </Typography>

        {loading && <Box sx={{ display: 'flex', justifyContent: 'center' }}><CircularProgress /></Box>}
        {error && <Typography color="error">Error: {error}</Typography>}

        {!loading && !error && summaries.length === 0 && (
          <Typography sx={{ color: 'text.secondary' }}>No backtest summaries found for comparison.</Typography>
        )}

        {!loading && !error && summaries.length > 0 && (
          <>
            <Paper sx={{ p: 3, mt: 3, mb: 3, backgroundColor: 'background.paper' }}>
              <Typography variant="h5" gutterBottom sx={{ color: 'text.primary' }}>
                Aggregated Summary Across {aggregatedSummary.total_runs} Runs
              </Typography>
              <Grid container spacing={2}>
                {Object.entries(aggregatedSummary).map(([key, value]) => (
                  <Grid item xs={12} sm={6} md={4} key={key}>
                    <Box sx={{ p: 2, border: '1px solid #333', borderRadius: '8px', backgroundColor: '#2c2c2c' }}>
                      <Typography variant="subtitle2" color="text.secondary">
                        {key.replace(/_/g, ' ')}
                      </Typography>
                      <Typography variant="h6" sx={{ fontWeight: 'bold', color: 'text.primary' }}>
                        {formatValue(value, key)}
                      </Typography>
                    </Box>
                  </Grid>
                ))}
              </Grid>
            </Paper>
            <ComparisonTable summaries={summaries} />
          </>
        )}
      </Box>
    </Container>
  );
};

export default ComparisonPage;
