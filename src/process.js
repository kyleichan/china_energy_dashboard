/**
 * Process raw China data to extract metrics
 * @param {Object[]} rawData - Array of raw data rows
 * @param {number} lastN - Number of recent years to include
 * @returns {Object[]} - Processed data summary per year
 */
function processChinaData(rawData, lastN) {
  // Map rows to objects with numeric values
  const mapped = rawData.map((row) => {
    const year = parseInt(row.year, 10);
    const gen = {
      total: toNumber(row.electricity_generation),
      coal: toNumber(row.coal_electricity),
      gas: toNumber(row.gas_electricity),
      oil: toNumber(row.oil_electricity),
      nuclear: toNumber(row.nuclear_electricity),
      hydro: toNumber(row.hydro_electricity),
      wind: toNumber(row.wind_electricity),
      solar: toNumber(row.solar_electricity),
      biofuel: toNumber(row.biofuel_electricity),
      other: toNumber(row.other_renewable_electricity)
    };
    return { year, generation: gen };
  });
  // Sort by year descending and take last N
  const recent = mapped
    .sort((a, b) => b.year - a.year)
    .slice(0, lastN)
    .map((item) => {
      const { year, generation } = item;
      const renewSum = sum(
        generation.hydro,
        generation.wind,
        generation.solar,
        generation.biofuel,
        generation.other
      );
      const total = generation.total;
      const shareRenew = total ? renewSum / total : null;
      const shareNon = total != null ? 1 - shareRenew : null;
      return {
        year,
        generation,
        share: {
          renewable: shareRenew,
          nonRenewable: shareNon
        },
        capacity: {} // TODO: capacity data not yet available
      };
    });
  return recent;
}

function toNumber(val) {
  const n = parseFloat(val);
  return isNaN(n) ? null : n;
}

function sum(...nums) {
  return nums.reduce((a, b) => a + (b || 0), 0);
}

module.exports = processChinaData;