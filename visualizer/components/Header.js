import React from 'react';
import { AppBar, Toolbar, Typography, Button } from '@mui/material';
import Link from 'next/link';

const Header = () => {
  return (
    <AppBar position="static" sx={{ marginBottom: '20px' }}>
      <Toolbar>
        <Typography variant="h5" component="div" sx={{ flexGrow: 1 }}>
          Backtest Visualizer
        </Typography>
        <Link href="/" passHref legacyBehavior>
          <Button color="inherit" sx={{ mr: 2 }}>
            Home
          </Button>
        </Link>
        <Link href="/comparison" passHref legacyBehavior>
          <Button color="inherit" sx={{ mr: 2 }}>
            Compare Backtests
          </Button>
        </Link>
        <Link href="/config" passHref legacyBehavior>
          <Button color="inherit" sx={{ mr: 2 }}>
            Config
          </Button>
        </Link>
        <Link href="/ping" passHref legacyBehavior>
          <Button color="inherit" sx={{ mr: 2 }}>
            Ping Logs
          </Button>
        </Link>
        <Link href="/logs" passHref legacyBehavior>
          <Button color="inherit" sx={{ mr: 2 }}>
            Server Logs
          </Button>
        </Link>

      </Toolbar>
    </AppBar>
  );
};

export default Header;
