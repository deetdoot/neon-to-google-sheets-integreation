# Neon to Google Sheets Sync

A robust, containerized Python application to sync data from a Neon PostgreSQL database table to a Google Sheet, with support for both one-time and continuous (interval-based) sync.

**Note:** As of July 13, 2025, Neon Postgres does not support Google Sheets connections natively. This project bridges that gap.

## Features

- **Continuous Sync**: Automatically sync data at configurable intervals
- **One-time Sync**: Perform a single sync operation and exit  
- **Docker Support**: Fully containerized with Docker and docker-compose
- **Modular Architecture**: Clean, maintainable code structure
- **Secure Credentials**: Environment-based configuration with .env support
- **Error Handling**: Robust error handling and graceful shutdowns
- **Health Checks**: Built-in health monitoring for Docker deployments

## Project Structure

```
neon-to-google-sheets/
├── src/                          # Source code
│   ├── core/                     # Core modules
│   │   ├── database.py          # Database connection and operations
│   │   └── sheets.py            # Google Sheets API operations
│   ├── sync/                     # Sync logic
│   │   ├── continuous_sync.py   # Continuous sync implementation
│   │   └── one_time_sync.py     # One-time sync implementation
│   └── utils/                    # Utility functions
├── scripts/                      # Entry point scripts
│   ├── continuous_sync.py       # Run continuous sync
│   ├── one_time_sync.py         # Run one-time sync
│   ├── test_database.py         # Test database connection
│   └── test_sheets.py           # Test Google Sheets connection
├── config/                       # Configuration files
├── data/                         # Persistent data (OAuth tokens)
├── docs/                         # Documentation
├── tests/                        # Test files
├── .env                          # Environment variables
├── .gitignore                    # Git ignore rules
├── .dockerignore                 # Docker ignore rules
├── Dockerfile                    # Docker container definition
├── docker-compose.yml           # Docker orchestration
├── docker-setup.sh              # Docker management script
├── requirements.txt              # Python dependencies
├── run_sync.py                   # Interactive sync runner
└── README.md                     # This file
```

## API Documentation

* [Neon Database API](https://neon.com/docs/connect/query-with-psql-editor)
* [Google Sheets API](https://developers.google.com/workspace/sheets/api/quickstart/python)
* [GSpread Documentation](https://docs.gspread.org/en/latest/user-guide.html)

## Environment Variables

Set the following environment variables in a `.env` file at the project root:

### Database Configuration

| Variable Name              | Description                                                                                   | Example Value |
|----------------------------|-----------------------------------------------------------------------------------------------|---------------|
| `PGHOST`                   | Neon database hostname (found in your Neon dashboard connection details)                     | `xs-white-cloud-pooler.c-2.us-east-2.aws.neon.tech` |
| `PGDATABASE`               | Name of your Neon database                                                                   | `neondb` |
| `PGUSER`                   | Username for Neon database authentication                                                    | `neondb_owner` |
| `PGPASSWORD`               | Password for the Neon database user                                                          | `your_password_here` |
| `PGSSLMODE`                | SSL mode for secure connection (required for Neon)                                           | `require` |
| `PGCHANNELBINDING`         | Channel binding mode for enhanced security                                                   | `require` |
| `TABLE_NAME`               | Name of the specific table you want to sync to Google Sheets                                 | `bookInstallation` |

### Google OAuth 2.0 Configuration

| Variable Name              | Description                                                                                   | Example Value |
|----------------------------|-----------------------------------------------------------------------------------------------|---------------|
| `CLIENT_ID`                | Google OAuth 2.0 client ID (from Google Cloud Console)                                      | `403552511240-xxx.apps.googleusercontent.com` |
| `PROJECT_ID`               | Google Cloud Project ID where your OAuth app is configured                                   | `xxx-xxx-320317` |
| `AUTH_URI`                 | Google OAuth 2.0 authorization endpoint                                                      | `https://accounts.google.com/o/oauth2/auth` |
| `TOKEN_URI`                | Google OAuth 2.0 token endpoint                                                              | `https://oauth2.googleapis.com/token` |
| `AUTH_PROVIDER_X509_CERT_URL` | Google's public key certificate URL                                                       | `https://www.googleapis.com/oauth2/v1/certs` |
| `CLIENT_SECRET`            | Google OAuth 2.0 client secret (from Google Cloud Console)                                  | `BACDSK-xxx` |
| `REDIRECT_URIS`            | Authorized redirect URIs for OAuth flow                                                      | `http://localhost` |

### Sync Configuration

| Variable Name              | Description                                                                                   | Example Value |
|----------------------------|-----------------------------------------------------------------------------------------------|---------------|
| `SYNC_INTERVAL_MINUTES`    | Interval between sync operations (for continuous sync)                                       | `2` |

### Google Sheets Configuration

| Variable Name              | Description                                                                                   | Example Value |
|----------------------------|-----------------------------------------------------------------------------------------------|---------------|
| `SPREADSHEET_NAME`         | Name of the Google Spreadsheet to create or update                                           | `NEW` |

## Recent Changes (v1.0.0)

### Code Reorganization
- **Modular Structure**: Moved all scripts to organized `src/` directory structure
- **Core Modules**: Created `src/core/database.py` and `src/core/sheets.py` for reusable components
- **Sync Logic**: Organized sync operations in `src/sync/` directory
- **Entry Scripts**: Added convenient entry points in `scripts/` directory
- **Docker Updates**: Updated Dockerfile and docker-compose.yml to use new structure

### New File Structure
- `src/core/`: Database and Google Sheets connection modules
- `src/sync/`: Continuous and one-time sync implementations  
- `scripts/`: Easy-to-use entry point scripts
- `backup/`: Old scripts moved for reference

### Backwards Compatibility
- `run_sync.py`: Updated to use new modular structure
- Docker containers: Updated to use new entry points
- Environment variables: No changes required

## Detailed Setup Instructions

### 1. Neon Database Setup
1. Log into your [Neon Console](https://console.neon.tech)
2. Navigate to your project dashboard
3. Click on "Connection Details" 
4. Copy the connection string components:
   - **Host**: Copy the hostname (e.g., `ep-xxx.pooler.c-2.us-east-2.aws.neon.tech`)
   - **Database**: Usually `neondb` or your custom database name
   - **User**: Usually `neondb_owner` or your custom username
   - **Password**: Your database password
5. Add these values to your `.env` file

### 2. Google Cloud Console Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select an existing one
3. Enable the Google Sheets API:
   - Navigate to "APIs & Services" → "Library"
   - Search for "Google Sheets API" and enable it
4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - Choose "Desktop application" as application type
   - Add `http://localhost` to authorized redirect URIs
   - Download the credentials JSON or copy the client ID and secret
5. Add the OAuth credentials to your `.env` file

### 3. Table Configuration
1. Identify the table name in your Neon database that you want to sync
2. Set the `TABLE_NAME` variable to match exactly (case-sensitive)
3. Ensure your table exists and has data to sync

### 4. Google Sheets Configuration
1. Set `SPREADSHEET_NAME` to your desired spreadsheet name
2. The script will create a new spreadsheet if it doesn't exist
3. Or connect to an existing spreadsheet with the same name

## Quick Start

### Option 1: Using Docker (Recommended)

1. **Clone and setup:**
   ```bash
   git clone <repository-url>
   cd neon-to-google-sheets
   cp .env.example .env  # Edit with your credentials
   ```

2. **Configure environment variables** in `.env` file (see Environment Variables section)

3. **Run with Docker:**
   ```bash
   # Continuous sync
   docker-compose up

   # One-time sync
   docker-compose run --rm neon-sync-once
   ```

### Option 2: Using Python directly

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment variables** in `.env` file

3. **Run sync:**
   ```bash
   # Interactive runner
   python run_sync.py

   # Direct execution
   python scripts/continuous_sync.py    # Continuous sync
   python scripts/one_time_sync.py      # One-time sync
   ```

### Option 3: Test connections first

```bash
# Test database connection
python scripts/test_database.py

# Test Google Sheets connection  
python scripts/test_sheets.py
```

## Usage Examples

### Continuous Sync
Automatically syncs data every X minutes (configured via `SYNC_INTERVAL_MINUTES`):

```bash
# Using Docker
docker-compose up

# Using Python
python scripts/continuous_sync.py
```

### One-time Sync
Performs a single sync operation and exits:

```bash
# Using Docker
docker-compose run --rm neon-sync-once

# Using Python
python scripts/one_time_sync.py
```

### Interactive Mode
Choose sync type interactively:

```bash
python run_sync.py
```

## Docker Management

Use the provided `docker-setup.sh` script for easy Docker management:

```bash
./docker-setup.sh
```

This provides options to:
- Start continuous sync
- Run one-time sync
- View logs
- Stop services
- Clean up containers
