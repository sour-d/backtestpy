import React from 'react';
import { AppBar, Toolbar, Typography, Select, MenuItem, Box, Button } from '@mui/material';
import Link from 'next/link';

const Header = ({ results, selectedResult, onSelectResult, showComparisonLink = true }) => {
  return (
    <AppBar position="static" sx={{ marginBottom: '20px' }}>
      <Toolbar>
        <Typography variant="h5" component="div" sx={{ flexGrow: 1 }}>
          Backtest Visualizer
        </Typography>
        <Link href="/config" passHref legacyBehavior>
            <Button color="inherit" sx={{ mr: 2 }}>
              Config
            </Button>
          </Link>
        <Link href="/logs" passHref legacyBehavior>
            <Button color="inherit" sx={{ mr: 2 }}>
              Logs
            </Button>
          </Link>
        {showComparisonLink && (
          <Link href="/comparison" passHref legacyBehavior>
            <Button color="inherit" sx={{ mr: 2 }}>
              Compare Backtests
            </Button>
          </Link>
        )}
        <Box sx={{ minWidth: 120 }}>
          <Select
            value={selectedResult || ''}
            onChange={(e) => onSelectResult(e.target.value)}
            displayEmpty
            inputProps={{ 'aria-label': 'Select result' }}
          >
            {results.map((result) => (
              <MenuItem key={result} value={result}>
                {result}
              </MenuItem>
            ))}
          </Select>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Header;
