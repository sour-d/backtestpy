import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#90caf9',
    },
    secondary: {
      main: '#f48fb1',
    },
    background: {
      default: '#121212',
      paper: '#1e1e1e',
    },
    text: {
      primary: '#e0e0e0',
      secondary: '#aaa',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h5: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 500,
    },
  },
  components: {
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#1e1e1e',
          boxShadow: 'none',
          borderBottom: '1px solid #333',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundColor: '#1e1e1e',
          boxShadow: '0px 2px 10px rgba(0, 0, 0, 0.5)',
          borderRadius: '8px',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundColor: '#2c2c2c',
          boxShadow: 'none',
          border: '1px solid #333',
          transition: 'transform 0.2s ease-in-out',
          '&:hover': {
            transform: 'translateY(-5px)',
            boxShadow: '0px 5px 15px rgba(0, 0, 0, 0.7)',
          },
        },
      },
    },
    MuiSelect: {
      styleOverrides: {
        select: {
          color: '#e0e0e0',
          '&:focus': {
            backgroundColor: 'transparent',
          },
        },
        icon: {
          color: '#e0e0e0',
        },
      },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        notchedOutline: {
          borderColor: '#333',
        },
        root: {
          '&:hover .MuiOutlinedInput-notchedOutline': {
            borderColor: '#555',
          },
          '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
            borderColor: '#90caf9',
          },
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderColor: '#333',
          color: '#e0e0e0',
        },
        head: {
          backgroundColor: '#333',
          color: '#e0e0e0',
          fontWeight: 'bold',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
        },
      },
    },
  },
});

export default theme;
