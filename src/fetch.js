const axios = require('axios');
const csv = require('csv-parser');

/**
 * Fetch raw China energy data from OWID CSV dataset
 * @returns {Promise<Object[]>} - Array of raw data rows for China
 */
async function fetchChinaRawData() {
  const url = 'https://raw.githubusercontent.com/owid/energy-data/master/owid-energy-data.csv';
  const response = await axios.get(url, { responseType: 'stream' });
  return new Promise((resolve, reject) => {
    const results = [];
    response.data
      .pipe(csv())
      .on('data', (row) => {
        if (row.iso_code === 'CHN') {
          results.push(row);
        }
      })
      .on('end', () => resolve(results))
      .on('error', (err) => reject(err));
  });
}

module.exports = fetchChinaRawData;