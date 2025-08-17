import React from 'react';
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper } from '@mui/material';

const ComparisonTable = ({ summaries }) => {
  if (!summaries || summaries.length === 0) {
    return null;
  }

  return (
    <TableContainer component={Paper}>
      <Table sx={{ minWidth: 650 }} aria-label="simple table">
        <TableHead>
          <TableRow>
            <TableCell>Symbol</TableCell>
            <TableCell>Timeframe</TableCell>
            <TableCell align="right">Net Profit</TableCell>
            <TableCell align="right">Total Trades</TableCell>
            <TableCell align="right">Win Rate (%)</TableCell>
            <TableCell align="right">Profit Factor</TableCell>
            <TableCell align="right">Max Drawdown (%)</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {summaries.map((summary) => (
            <TableRow key={`${summary.symbol}-${summary.timeframe}`}>
              <TableCell component="th" scope="row">
                {summary.symbol}
              </TableCell>
              <TableCell>{summary.timeframe}</TableCell>
              <TableCell align="right">{summary.net_profit.toFixed(2)}</TableCell>
              <TableCell align="right">{summary.total_trades}</TableCell>
              <TableCell align="right">{summary.win_rate.toFixed(2)}</TableCell>
              <TableCell align="right">{summary.profit_factor.toFixed(2)}</TableCell>
              <TableCell align="right">{summary.max_drawdown_pct.toFixed(2)}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export default ComparisonTable;
