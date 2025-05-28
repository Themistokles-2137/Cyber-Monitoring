# Indian Cyber Incident Monitor (ICIM)

A comprehensive platform for collecting, analyzing, and visualizing cyber security incidents specific to the Indian cyber landscape. This tool assists the National Critical Information Infrastructure Protection Centre (NCIIPC) in monitoring and sharing critical cyber threat intelligence with stakeholders.

![Dashboard Screenshot](https://cdn.example.com/icim-dashboard.png) *(Replace with an actual screenshot)*

## 🔍 Overview

The Indian Cyber Incident Monitor (ICIM) is designed to address the growing need for specialized cyber threat intelligence focused on the Indian cyber space. It leverages machine learning, web scraping, and data visualization to provide actionable intelligence on emerging threats and vulnerabilities affecting Indian organizations and critical infrastructure.

### Key Features

- **Automated Data Collection**: Scrapes and collects cyber incident information from various sources (news sites, social media, paste sites)
- **ML-Powered Classification**: Automatically categorizes incidents by sector, severity, and relevance
- **Comprehensive Dashboard**: Visual representation of incident trends, sector distribution, and severity metrics
- **Advanced Search & Filtering**: Find specific incidents based on multiple criteria
- **Source Management**: Track and evaluate the reliability of different information sources
- **Interactive Visualizations**: Charts and graphs for data-driven decision making

## 🛠️ Technology Stack

- **Backend**: Python, Flask
- **Database**: PostgreSQL
- **Machine Learning**: scikit-learn, NLTK
- **Web Scraping**: BeautifulSoup4, Trafilatura, Requests
- **Frontend**: Bootstrap, Chart.js
- **Deployment**: Gunicorn

## 🚀 Installation & Setup

### Prerequisites

- Python 3.8+
- PostgreSQL 13+
- pip

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/indian-cyber-incident-monitor.git
   cd indian-cyber-incident-monitor
   ```

2. **Set up a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file with the following:
   ```
   DATABASE_URL=postgresql://username:password@localhost:5432/icim
   SESSION_SECRET=your_secret_key
   FLASK_DEBUG=1
   ```

5. **Initialize the database**
   ```bash
   # Create the database in PostgreSQL
   createdb icim  # May vary based on your PostgreSQL setup
   
   # Run database initialization script
   python init_db.py
   ```

6. **Run the application**
   ```bash
   python main.py
   # or
   gunicorn --bind 0.0.0.0:5000 main:app
   ```

7. **Access the application**
   Open your browser and visit: `http://localhost:5000`

## 📋 Project Structure

```
.
├── ml/                     # Machine learning models and algorithms
│   ├── incident_classifier.py
│   └── source_classifier.py
├── routes/                 # API and web routes
│   ├── api_routes.py       # API endpoints
│   ├── dashboard_routes.py # Dashboard visualizations
│   └── main_routes.py      # Main application routes
├── scrapers/               # Web scraping modules
│   ├── news_scraper.py
│   ├── pastebin_scraper.py
│   └── twitter_scraper.py
├── static/                 # Frontend assets
│   ├── css/                # Stylesheet files
│   └── js/                 # JavaScript files
├── templates/              # HTML templates
├── utils/                  # Utility functions
│   ├── nlp_processor.py    # NLP utilities for text processing
│   └── text_extractor.py   # Text extraction utilities
├── app.py                  # Flask application setup
├── config.py               # Configuration settings
├── init_db.py              # Database initialization
├── main.py                 # Application entry point
├── models.py               # Database models
└── seed_data.py            # Sample data for testing
```

## 🧠 Machine Learning Components

### Source Classifier

The Source Classifier model evaluates and categorizes potential sources of cyber incident information. It uses:

- **TF-IDF Vectorization**: Transforms text into numerical features
- **Support Vector Machine (SVM)**: Classifies sources based on their relevance to Indian cybersecurity

### Incident Classifier

The Incident Classifier analyzes incident descriptions to categorize them by:

- **Sector**: Identifies affected sectors (finance, healthcare, government, etc.)
- **Severity**: Assigns criticality levels based on impact and scope
- **Attribution**: Attempts to identify threat actors when possible

## 🕸️ Web Scraping Capabilities

The system implements specialized scrapers for different types of sources:

- **News Scraper**: Collects information from cyber security news websites
- **Twitter Scraper**: Gathers data from relevant Twitter accounts and hashtags
- **Pastebin Scraper**: Monitors paste sites for data leaks and hacker communications

Each scraper implements proper rate limiting, content filtering, and data normalization to ensure quality and compliance.

## 📊 Visualization Features

The dashboard presents actionable intelligence through several visualizations:

- **Incident Trend**: Time-based graph of incident frequency
- **Sector Distribution**: Breakdown of incidents by affected sector
- **Severity Distribution**: Incidents categorized by severity level
- **Source Reliability**: Evaluation of information sources

## 🔄 API Documentation

The system provides a RESTful API for integration with other security tools:

### GET /api/incidents
Retrieve a list of incidents with optional filtering.

**Parameters:**
- `page`: Page number (default: 1)
- `per_page`: Results per page (default: 10)
- `sector`: Filter by sector
- `severity`: Filter by severity
- `start_date`: Filter by date range start (YYYY-MM-DD)
- `end_date`: Filter by date range end (YYYY-MM-DD)

**Response:**
```json
{
  "incidents": [
    {
      "id": 1,
      "title": "Major Bank Data Breach",
      "description": "...",
      "discovered_date": "2023-06-15T14:30:00",
      "severity": "High",
      "sector": "Finance",
      "source": "CERT-In",
      "source_url": "https://example.com/incident1"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total": 42,
    "pages": 5
  }
}
```

### GET /api/sectors
Get sector distribution statistics.

### GET /api/severities
Get severity distribution statistics.

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🙏 Acknowledgements

- [CERT-In](https://www.cert-in.org.in/) for providing reference data
- [NCIIPC](https://nciipc.gov.in/) for domain expertise guidance
- All open-source libraries and tools used in this project