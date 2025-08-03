import React from 'react';
import { Card, CardContent, Typography, Grid } from '@mui/material';

const SummaryCards = ({ summary }) => {
  return (
    <Grid container spacing={2} sx={{ marginBottom: '20px' }}>
      {Object.entries(summary).map(([key, value]) => {
        if (typeof value !== 'object') {
          return (
            <Grid item xs={12} sm={6} md={4} key={key}>
              <Card sx={{ backgroundColor: '#1e1e1e', color: '#e0e0e0' }}>
                <CardContent>
                  <Typography variant="subtitle1" color="text.secondary" gutterBottom sx={{ color: '#aaa' }}>
                    {key.replace(/_/g, ' ')}
                  </Typography>
                  <Typography variant="h6" component="div">
                    {typeof value === 'number'
                      ? value.toLocaleString(undefined, {
                          maximumFractionDigits: 2,
                        })
                      : value.toLocaleString()}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          );
        }
        return null;
      })}
    </Grid>
  );
};

export default SummaryCards;
