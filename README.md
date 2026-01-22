# SciENcv Biosketch Creator

A web application that parses NIH biosketch Word documents and automates the creation of SciENcv entries at https://www.ncbi.nlm.nih.gov/labs/sciencv/

## Features

- **Document Parsing**: Extracts all sections from NIH biosketch .docx files
  - Header information (name, eRA Commons username, position)
  - Education/Training table
  - Section A: Personal Statement with citations
  - Section B: Positions and Honors
  - Section C: Contributions to Science with citations

- **Web Interface**: Upload, review, and edit parsed data before automation

- **Browser Automation**: Uses Playwright to fill SciENcv forms
  - Manual login support (handles 2FA via Login.gov/eRA Commons)
  - Session persistence for repeated use
  - Progress tracking and status updates

## Quick Start

### Prerequisites

- Python 3.9+
- pip (Python package manager)

### Installation

1. Clone or download this repository

2. Create a virtual environment and install dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Install Playwright browsers:
   ```bash
   playwright install chromium
   ```

### Running the Web Application

```bash
python run.py
```

Then open http://localhost:5000 in your browser.

### Command-Line Interface

Parse a biosketch document:
```bash
python cli.py parse biosketch.docx
python cli.py parse biosketch.docx -o output.json -v
```

Parse and automate SciENcv:
```bash
python cli.py automate biosketch.docx
```

## Usage

### Web Interface

1. **Upload**: Click "Upload" and select your NIH biosketch .docx file
2. **Review**: Check the parsed data for accuracy, make edits if needed
3. **Automate**: Click "Start SciENcv Automation"
4. **Login**: A browser window opens - log in to SciENcv manually (2FA supported)
5. **Watch**: The automation fills in your biosketch entries
6. **Verify**: Review the completed entries in SciENcv

### Biosketch Format

The parser expects a standard NIH biosketch format with:
- Header fields (NAME:, eRA COMMONS USER NAME:, POSITION TITLE:)
- Education/Training table
- Section A. Personal Statement
- Section B. Positions, Scientific Appointments, and Honors
- Section C. Contributions to Science

## Project Structure

```
SciENcv/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── config.py             # Configuration
│   ├── parser/               # Document parsing
│   │   ├── models.py         # Data classes
│   │   ├── biosketch_parser.py
│   │   └── citation_parser.py
│   ├── automation/           # Browser automation
│   │   ├── sciencv_filler.py
│   │   ├── auth_handler.py
│   │   └── selectors.py
│   ├── api/
│   │   └── routes.py         # API endpoints
│   └── templates/            # HTML templates
├── tests/
│   └── test_parser.py
├── requirements.txt
├── run.py                    # Run development server
├── cli.py                    # Command-line interface
├── Dockerfile
└── docker-compose.yml
```

## Running Tests

```bash
python -m pytest tests/ -v
```

## Docker Deployment

```bash
docker-compose up --build
```

## Security Notes

- Login credentials are NEVER stored - you authenticate directly with Login.gov/eRA Commons
- Browser sessions are stored locally for convenience but can be deleted anytime
- The application runs locally - your biosketch data never leaves your machine

## Troubleshooting

### SciENcv UI Changes
If SciENcv updates their interface, you may need to update the CSS selectors in `app/automation/selectors.py`.

### Login Issues
- Ensure you have a valid eRA Commons or NCBI account
- Complete 2FA within 5 minutes
- If session expires, restart the automation

### Parsing Issues
- Ensure your biosketch follows the standard NIH format
- Check that section headers match expected patterns (A., B., C.)
- Review the JSON output for any parsing errors

## License

MIT License
