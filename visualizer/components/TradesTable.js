import React, { useState } from 'react';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow, 
  Paper, 
  Typography, 
  Button, 
  Box 
} from '@mui/material';
import { KeyboardArrowDown, KeyboardArrowUp } from '@mui/icons-material';

const TradesTable = ({ tradeData }) => {
  const [isCollapsed, setIsCollapsed] = useState(false);

  return (
    <Paper sx={{ p: 2, mb: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6" component="h2">
          Trade History ({tradeData.length} trades)
        </Typography>
        <Button 
          onClick={() => setIsCollapsed(!isCollapsed)}
          variant="outlined"
          color="primary"
          startIcon={isCollapsed ? <KeyboardArrowDown /> : <KeyboardArrowUp />}
        >
          {isCollapsed ? 'Show' : 'Hide'}
        </Button>
      </Box>
      {!isCollapsed && (
        <TableContainer>
          <Table sx={{ minWidth: 650 }} aria-label="trade history table">
            <TableHead>
              <TableRow>
                <TableCell>Type</TableCell>
                <TableCell>Entry Date</TableCell>
                <TableCell>Exit Date</TableCell>
                <TableCell align="right">Entry Price</TableCell>
                <TableCell align="right">Exit Price</TableCell>
                <TableCell align="right">Quantity</TableCell>
                <TableCell align="right">P&L</TableCell>
                <TableCell align="right">P&L %</TableCell>
                <TableCell>Exit Reason</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {tradeData.map((trade, index) => (
                <TableRow
                  key={index}
                  sx={{
                    '&:last-child td, &:last-child th': { border: 0 },
                    backgroundColor: 'background.paper',
                    '&:hover': { backgroundColor: '#333' }
                  }}
                >
                  <TableCell component="th" scope="row">
                    <Typography 
                      variant="body2"
                      sx={{
                        padding: '4px 8px',
                        borderRadius: '4px',
                        fontSize: '0.85rem',
                        fontWeight: 'bold',
                        backgroundColor: trade.type === 'buy' ? '#26a69a' : '#ef5350',
                        color: 'white',
                        display: 'inline-block'
                      }}
                    >
                      {trade.type?.toUpperCase()}
                    </Typography>
                  </TableCell>
                  <TableCell sx={{ fontSize: '0.9rem' }}>
                    {new Date(trade.entry_date).toLocaleDateString('en-US', {
                      day: 'numeric',
                      month: 'short',
                      year: 'numeric'
                    })}
                  </TableCell>
                  <TableCell sx={{ fontSize: '0.9rem' }}>
                    {new Date(trade.exit_date).toLocaleDateString('en-US', {
                      day: 'numeric',
                      month: 'short',
                      year: 'numeric'
                    })}
                  </TableCell>
                  <TableCell align="right" sx={{ fontFamily: 'monospace' }}>
                    ${parseFloat(trade.entry_price).toFixed(2)}
                  </TableCell>
                  <TableCell align="right" sx={{ fontFamily: 'monospace' }}>
                    ${parseFloat(trade.exit_price).toFixed(2)}
                  </TableCell>
                  <TableCell align="right" sx={{ fontFamily: 'monospace' }}>
                    {parseFloat(trade.quantity).toFixed(4)}
                  </TableCell>
                  <TableCell 
                    align="right" 
                    sx={{
                      fontFamily: 'monospace',
                      fontWeight: 'bold',
                      color: parseFloat(trade.net_profit_loss) >= 0 ? '#26a69a' : '#ef5350',
                    }}
                  >
                    ${parseFloat(trade.net_profit_loss).toFixed(2)}
                  </TableCell>
                  <TableCell 
                    align="right" 
                    sx={{
                      fontFamily: 'monospace',
                      fontWeight: 'bold',
                      color: parseFloat(trade.net_profit_loss_pct) >= 0 ? '#26a69a' : '#ef5350',
                    }}
                  >
                    {parseFloat(trade.net_profit_loss_pct).toFixed(2)}%
                  </TableCell>
                  <TableCell sx={{ fontSize: '0.85rem', color: 'text.secondary' }}>
                    {trade.exit_reason}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Paper>
  );
};

export default TradesTable;
