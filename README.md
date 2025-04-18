# China Clean Energy Data Tracker

A tool for collecting, processing, and querying data on China's clean energy sector. This project provides a modular, extensible CLI and API to fetch, normalize, and serve data from various sources.

## Features
- Data collection from multiple sources (e.g., government agencies, research institutions, open databases)
- Data normalization, validation, and storage
- Command-line interface for fetching and querying data
- Local API server to expose data endpoints
- Modular architecture for adding new data sources and processing pipelines

## Getting Started

### Prerequisites
- Node.js (v14 or higher)
- npm or yarn
- (Optional) Python 3.x if using supplementary scraping scripts

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/china-clean-energy-data-tracker.git
   cd china-clean-energy-data-tracker
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Configure environment variables:
   - Create a `.env` file in the project root.
   - Copy from `.env.example` (if available) and set values:
     ```dotenv
     DATABASE_URL=postgres://user:pass@localhost:5432/clean_energy
     DATA_SOURCE_API_KEY=your_api_key_here
     ```

## Usage

### Fetch Data
Fetch and store the latest data:
```bash
npm run fetch
# or
node index.js fetch
```

### Start API Server
Launch the local server to expose endpoints:
```bash
npm start
# or
node index.js serve
```

### Query Data
- Command-line:
  ```bash
  node index.js query --year 2020 --metric solar_capacity
  ```
- HTTP API:
  ```http
  GET /api/data?year=2020&metric=solar_capacity
  ```

## Project Structure
```
.
├── data/               # Raw and processed data files
├── src/                # Source code
│   ├── index.js        # Entry point and CLI/router
│   ├── fetch.js        # Data fetching logic
│   ├── process.js      # Data normalization and processing
│   └── utils/          # Utility modules
├── scripts/            # Helper scripts (e.g., web scraping)
├── tests/              # Test suites
├── .env.example        # Example environment variables
└── README.md
```

## Data Sources
- National Energy Administration of China (http://www.nea.gov.cn/)
- International Renewable Energy Agency (IRENA) (https://www.irena.org/)
- OpenEI (https://openei.org/)

## Contributing
Contributions are welcome! Please follow these steps:
1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "Add your feature"`
4. Push to your branch: `git push origin feature/your-feature`
5. Open a Pull Request.

## License
This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Authors
- Your Name (<your.email@example.com>)