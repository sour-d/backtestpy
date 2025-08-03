import React from 'react';
import { AppBar, Toolbar, Typography, Select, MenuItem, Box } from '@mui/material';

const Header = ({ results, selectedResult, onSelectResult }) => {
  return (
    <AppBar position="static" sx={{ backgroundColor: 'unset', marginBottom: '20px' }}>
      <Toolbar>
        <Typography variant="h5" component="div" sx={{ flexGrow: 1, color: '#e0e0e0' }}>
          Backtest Visualizer
        </Typography>
        <Box sx={{ minWidth: 120 }}>
          <Select
            value={selectedResult || ''}
            onChange={(e) => onSelectResult(e.target.value)}
            displayEmpty
            inputProps={{ 'aria-label': 'Select result' }}
            sx={{
              color: '#e0e0e0',
              '.MuiOutlinedInput-notchedOutline': {
                borderColor: '#333',
              },
              '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                borderColor: '#555',
              },
              '&:hover .MuiOutlinedInput-notchedOutline': {
                borderColor: '#444',
              },
              '.MuiSvgIcon-root': {
                color: '#e0e0e0',
              },
            }}
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
