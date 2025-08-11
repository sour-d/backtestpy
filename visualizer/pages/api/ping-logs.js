import fs from 'fs';
import path from 'path';

export default function handler(req, res) {
  const logFilePath = path.resolve(process.cwd(), '../../logs/ping.txt');

  try {
    const logData = fs.readFileSync(logFilePath, 'utf8');
    const logs = logData.split('\n').filter(line => line.trim() !== '');
    res.status(200).json({ logs });
  } catch (error) {
    res.status(500).json({ error: 'Failed to read ping log file' });
  }
}
