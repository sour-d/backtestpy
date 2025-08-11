import { useState, useEffect } from 'react';
import Header from '../components/Header';

const LogsPage = () => {
  const [logs, setLogs] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const res = await fetch('/api/logs');
        const data = await res.json();
        if (res.ok) {
          setLogs(data.logs);
        } else {
          setError(data.error);
        }
      } catch (err) {
        setError('Failed to fetch logs');
      }
    };

    fetchLogs();
  }, []);

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <Header />
      <main className="p-4 md:p-8">
        <h1 className="text-2xl font-bold mb-4">Live Trading Logs</h1>
        {error && <p className="text-red-500">{error}</p>}
        <div className="bg-gray-800 p-4 rounded-lg">
          <pre className="whitespace-pre-wrap break-all">
            {logs.length > 0 ? (
              logs.map((log, index) => (
                <div key={index} className="border-b border-gray-700 py-1">{log}</div>
              ))
            ) : (
              <p>No logs found.</p>
            )}
          </pre>
        </div>
      </main>
    </div>
  );
};

export default LogsPage;
