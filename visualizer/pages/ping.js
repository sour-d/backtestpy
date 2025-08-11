import { useState, useEffect } from 'react';
import Header from '../components/Header';

const PingPage = () => {
  const [pings, setPings] = useState([]);
  const [error, setError] = useState(null);

  const fetchPings = async () => {
    try {
      const res = await fetch('/api/ping-logs');
      const data = await res.json();
      if (res.ok) {
        setPings(data.logs.reverse());
      } else {
        setError(data.error);
      }
    } catch (err) {
      setError('Failed to fetch pings');
    }
  };

  useEffect(() => {
    fetchPings();
  }, []);

  const handlePing = async () => {
    try {
      const res = await fetch('/api/ping', { method: 'POST' });
      if (res.ok) {
        fetchPings();
      }
    } catch (err) {
      setError('Failed to send ping');
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <Header />
      <main className="p-4 md:p-8">
        <h1 className="text-2xl font-bold mb-4">Ping</h1>
        <button
          onClick={handlePing}
          className="bg-blue-600 px-4 py-2 rounded-lg mb-4"
        >
          Send Ping
        </button>
        {error && <p className="text-red-500">{error}</p>}
        <div className="bg-gray-800 p-4 rounded-lg">
          <h2 className="text-xl font-semibold mb-2">Ping Logs</h2>
          <pre className="whitespace-pre-wrap break-all">
            {pings.length > 0 ? (
              pings.map((ping, index) => (
                <div key={index} className="border-b border-gray-700 py-1">{ping}</div>
              ))
            ) : (
              <p>No pings found.</p>
            )}
          </pre>
        </div>
      </main>
    </div>
  );
};

export default PingPage;
