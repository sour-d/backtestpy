import { useState, useEffect } from 'react';
import Header from '../components/Header';

const ConfigPage = () => {
  const [mode, setMode] = useState('');

  useEffect(() => {
    const savedMode = localStorage.getItem('visualizer_mode') || 'backtest';
    setMode(savedMode);
  }, []);

  const handleModeChange = (newMode) => {
    setMode(newMode);
    localStorage.setItem('visualizer_mode', newMode);
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <Header />
      <main className="p-4 md:p-8">
        <h1 className="text-2xl font-bold mb-4">Configuration</h1>
        <div className="bg-gray-800 p-4 rounded-lg">
          <h2 className="text-xl font-semibold mb-2">Select Mode</h2>
          <div className="flex space-x-4">
            <button
              onClick={() => handleModeChange('backtest')}
              className={`px-4 py-2 rounded-lg ${
                mode === 'backtest' ? 'bg-blue-600' : 'bg-gray-700'
              }`}
            >
              Backtest
            </button>
            <button
              onClick={() => handleModeChange('live')}
              className={`px-4 py-2 rounded-lg ${
                mode === 'live' ? 'bg-green-600' : 'bg-gray-700'
              }`}
            >
              Live
            </button>
          </div>
          <p className="mt-4">Currently selected mode: <span className="font-bold">{mode}</span></p>
        </div>
      </main>
    </div>
  );
};

export default ConfigPage;
