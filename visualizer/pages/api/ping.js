import fs from 'fs';
import path from 'path';

export default function handler(req, res) {
  if (req.method === 'POST') {
    const logFilePath = path.resolve(process.cwd(), '../logs/ping.txt');
    const now = new Date();
    const istTime = now.toLocaleString('en-US', { timeZone: 'Asia/Kolkata' });

    try {
      let existingLogs = [];
      if (fs.existsSync(logFilePath)) {
        const fileContent = fs.readFileSync(logFilePath, 'utf8');
        existingLogs = fileContent.split('\n').filter(line => line.trim() !== '');
      }

      // Keep only the last 99 logs to make space for the new one (total 100)
      if (existingLogs.length >= 100) {
        existingLogs = existingLogs.slice(existingLogs.length - 99);
      }

      existingLogs.push(istTime);

      fs.writeFileSync(logFilePath, existingLogs.join('\n') + '\n');
      res.status(200).json({ message: 'Ping logged successfully' });
    } catch (error) {
      res.status(500).json({ message: 'Failed to write to ping log file', error });
    }
  } else {
    res.status(405).json({ error: 'Method not allowed' });
  }
}
