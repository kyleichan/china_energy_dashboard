#!/usr/bin/env node
const { program } = require('commander');
const fs = require('fs');
const path = require('path');
const fetchChinaRawData = require('./fetch');
const processChinaData = require('./process');

program.version('0.1.0');

program
  .command('fetch')
  .description('Fetch and process latest China energy data')
  .option('-y, --years <number>', 'Number of years to retrieve', parseInt, 5)
  .action(async (opts) => {
    console.log('Fetching data...');
    let rawData;
    try {
      rawData = await fetchChinaRawData();
    } catch (err) {
      console.error('Error fetching data:', err.message);
      process.exit(1);
    }
    console.log('Processing data...');
    const summary = processChinaData(rawData, opts.years);
    const outDir = path.join(process.cwd(), 'data');
    if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });
    const outFile = path.join(outDir, 'china-energy-summary.json');
    fs.writeFileSync(outFile, JSON.stringify(summary, null, 2));
    console.log(`Summary written to ${outFile}`);
  });

program
  .command('query')
  .description('Query processed data')
  .option('-f, --file <path>', 'Summary JSON file path', path.join(process.cwd(), 'data', 'china-energy-summary.json'))
  .option('-y, --year <year>', 'Year to query', parseInt)
  .action((opts) => {
    if (!fs.existsSync(opts.file)) {
      console.error(`File not found: ${opts.file}`);
      process.exit(1);
    }
    const summary = JSON.parse(fs.readFileSync(opts.file));
    if (opts.year) {
      const entry = summary.find((d) => d.year === opts.year);
      if (!entry) {
        console.log(`No data for year ${opts.year}`);
      } else {
        console.log(JSON.stringify(entry, null, 2));
      }
    } else {
      console.log(JSON.stringify(summary, null, 2));
    }
  });

program.parse(process.argv);