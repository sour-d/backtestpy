import { promises as fs } from 'fs';
import path from 'path';
import Papa from 'papaparse';

export default async function handler(req, res) {
  const dataDir = path.join(process.cwd(), '..', 'data');
  const summaryDir = path.join(dataDir, 'summary');
  const resultDir = path.join(dataDir, 'result');
  const processedDir = path.join(dataDir, 'processed');

  if (req.method === 'GET') {
    if (req.query.name) {
      // Handle request for specific result data
      const resultName = req.query.name;
      const summaryPath = path.join(summaryDir, `${resultName}.json`);
      const tradesPath = path.join(resultDir, `${resultName}.csv`);

      try {
        const summary = JSON.parse((await fs.readFile(summaryPath, 'utf8')));
        const tradesCsv = await fs.readFile(tradesPath, 'utf8');

        const trades = Papa.parse(tradesCsv.trim(), { header: true }).data;

        // Extract symbol and timeframe from resultName for raw data lookup
        // resultName format: "BTC-USDT_1d_2024"
        const parts = resultName.split('_');
        const symbolPart = parts[0]; // e.g., "BTC-USDT"
        const timeframe = parts[1]; // e.g., "1d"

        // Convert "BTC-USDT" to "btcusdt" for processed file lookup
        const processedSymbol = symbolPart.toLowerCase().replace('-', '');
        const rawDataFileName = `${processedSymbol}_${timeframe}.csv`;
        const rawDataPath = path.join(processedDir, rawDataFileName);

        let rawData = [];
        if (await fs.access(rawDataPath).then(() => true).catch(() => false)) {
          const rawDataCsv = await fs.readFile(rawDataPath, 'utf8');
          rawData = Papa.parse(rawDataCsv.trim(), { header: true }).data;
        }

        res.status(200).json({ summary, trades, rawData });
      } catch (error) {
        console.error('Error fetching result data:', error);
        res.status(404).json({ message: 'Result data not found' });
      }
    } else {
      // Handle request for list of all results
      try {
        const files = await fs.readdir(summaryDir);
        const results = files.filter(file => file.endsWith('.json')).map(file => file.replace('.json', ''));
        res.status(200).json(results);
      } catch (error) {
        console.error('Error listing results:', error);
        res.status(500).json({ message: 'Unable to list results' });
      }
    }
  } else {
    res.status(405).json({ message: 'Method Not Allowed' });
  }
}