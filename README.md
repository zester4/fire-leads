# FireLeads: Advanced Lead Extraction System

**FireLeads** is a production-ready, highly efficient lead extraction system powered by **Firecrawl v2**. Designed for robust and validated lead generation, this system leverages the latest web scraping technologies and intelligent processing to deliver high-quality leads.

## Installation and Usage:

### 1. Install dependencies
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure
```bash
cp .env.example .env
# Edit .env and add your FIRECRAWL_API_KEY
```

### 3. Run extraction
```bash
python main.py --domain https://example.com
```

### 4. Advanced usage
```bash
python main.py --domain https://example.com --max-pages 300 --output example_leads
```

### 5. With CRM push
```bash
python main.py --domain https://example.com --push-hubspot
```

## Output Files:
The system creates 4 output files in the `output/` directory:

*   `leads.json` - Full lead data with all fields
*   `leads.csv` - Complete CSV with all columns
*   `leads_emails.txt` - Plain text file with one email per line
*   `leads_emails.csv` - Simple CSV with just emails

## Key Features:
✅ Firecrawl v2 SDK - Uses latest official Python SDK
✅ Batch scraping - Processes multiple URLs simultaneously
✅ Smart filtering - Identifies contact/team pages automatically
✅ Advanced email validation - DNS and deliverability checks
✅ Multiple output formats - JSON, CSV, and TXT
✅ Progress tracking - Real-time progress bars
✅ CRM integration - Push to HubSpot and Instantly
✅ Error handling - Robust retry logic and fallbacks
✅ Deduplication - Automatically removes duplicate emails

## Technologies Used

*   **Firecrawl v2 SDK**: Core web scraping engine.
*   **Python-dotenv**: For managing environment variables securely.
*   **Email-validator**: For robust email format and DNS validation.
*   **Dnspython**: Dependency for advanced DNS checks in email validation.
*   **Tqdm**: For displaying intelligent progress bars.
*   **Requests**: For making HTTP requests.

## Getting Started

*(Further instructions on installation, configuration, and usage will be added here.)*