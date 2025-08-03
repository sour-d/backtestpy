
import React from 'react';
import { AreaChart, BarChart, Card, Title } from '@tremor/react';

const valueFormatter = (number) => `$${new Intl.NumberFormat('us').format(number).toString()}`;

const CandlestickChart = ({ data, title }) => {
  // Candlestick chart not directly available in Tremor, using AreaChart as a placeholder
  const chartData = data.map(d => ({
    date: d.date,
    'Price': d.close,
  }));

  return (
    <Card>
      <Title>{title}</Title>
      <AreaChart
        className="h-72 mt-4"
        data={chartData}
        index="date"
        categories={['Price']}
        colors={['indigo']}
        yAxisWidth={60}
      />
    </Card>
  );
};

const DrawdownChart = ({ trades }) => {
  const drawdownData = trades.map(trade => ({
    date: new Date(trade.exit_date).toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric' }),
    'Drawdown': trade.drawdown,
  }));

  return (
    <Card>
      <Title>Drawdown</Title>
      <AreaChart
        className="h-72 mt-4"
        data={drawdownData}
        index="date"
        categories={['Drawdown']}
        colors={['red']}
        yAxisWidth={60}
        valueFormatter={valueFormatter}
      />
    </Card>
  );
};

const ProfitLossChart = ({ trades }) => {
  const pnlData = trades.map(trade => ({
    date: new Date(trade.exit_date).toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric' }),
    'Profit/Loss': trade.net_profit_loss,
  }));

  return (
    <Card>
      <Title>Profit/Loss</Title>
      <BarChart
        className="h-72 mt-4"
        data={pnlData}
        index="date"
        categories={['Profit/Loss']}
        colors={['emerald']}
        yAxisWidth={60}
        valueFormatter={valueFormatter}
      />
    </Card>
  );
};

export { CandlestickChart, DrawdownChart, ProfitLossChart };
