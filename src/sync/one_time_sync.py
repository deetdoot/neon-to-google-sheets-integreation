#!/usr/bin/env python3
"""
Neon to Google Sheets One-Time Sync Script
==========================================

This script performs a single sync operation from Neon PostgreSQL database
to Google Sheets and then exits.
"""

import os
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime

# Import from our modular structure
from src.core.database import DatabaseConnection
from src.core.sheets import GoogleSheetsConnection

# Load environment variables
load_dotenv()

class OneTimeSyncToSheets:
    def __init__(self):
        """Initialize the sync class with database and sheets connections"""
        self.db = DatabaseConnection()
        self.sheets = GoogleSheetsConnection()
        self.table_name = os.getenv('TABLE_NAME')
        self.df = None
    
    def validate_environment(self):
        """Validate required environment variables"""
        required_vars = [
            'PGHOST', 'PGDATABASE', 'PGUSER', 'PGPASSWORD', 'TABLE_NAME',
            'CLIENT_ID', 'CLIENT_SECRET', 'PROJECT_ID'
        ]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            print(f"Missing environment variables: {', '.join(missing_vars)}")
            return False
        return True
    
    def connect_to_services(self):
        """Connect to database and Google Sheets"""
        print("Connecting to services...")
        
        # Connect to database
        if not self.db.connect():
            print("Failed to connect to database")
            return False
        
        # Validate table exists
        if not self.db.table_exists(self.table_name):
            print(f"Table '{self.table_name}' not found in database")
            return False
        
        print(f"Successfully connected to database and found table '{self.table_name}'")
        
        # Connect to Google Sheets
        if not self.sheets.connect():
            print("Failed to connect to Google Sheets")
            return False
        
        # Setup worksheets
        if not self.sheets.setup_worksheets(self.table_name):
            print("Failed to setup Google Sheets worksheets")
            return False
        
        print(f"Successfully connected to Google Sheets")
        return True
    
    def download_and_upload_data(self):
        """Download data from database and upload to Google Sheets"""
        print(f"Downloading data from table '{self.table_name}'...")
        
        # Download data from database
        self.df = self.db.get_table_data(self.table_name)
        
        if self.df is None or len(self.df) == 0:
            print("No data found in table")
            return False
        
        print(f"Successfully downloaded {len(self.df)} rows and {len(self.df.columns)} columns")
        print(f"Data shape: {self.df.shape}")
        
        # Show first few rows for verification
        print(f"\nFirst 3 rows preview:")
        print(self.df.head(3).to_string(index=False))
        
        # Upload to Google Sheets
        print("\nUploading data to Google Sheets...")
        worksheet_name = f"{self.table_name}_data"
        
        if not self.sheets.update_data_worksheet(self.df, worksheet_name):
            print("Failed to upload data to Google Sheets")
            return False
        
        # Update metadata
        metadata = {
            "Last Sync Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Source Table": self.table_name,
            "Total Rows": len(self.df),
            "Total Columns": len(self.df.columns),
            "Data Worksheet": worksheet_name,
            "Sync Type": "One-time"
        }
        
        if not self.sheets.update_metadata_worksheet(metadata):
            print("Failed to update metadata")
            return False
        
        print(f"Successfully uploaded {len(self.df)} rows to Google Sheets")
        print(f"Data uploaded to worksheet: '{worksheet_name}'")
        print(f"Spreadsheet URL: {self.sheets.get_spreadsheet_url()}")
        
        return True
    
    def sync_data(self):
        """Main method to execute the complete sync process"""
        print("Starting One-Time Neon to Google Sheets Sync")
        print("=" * 60)
        
        # Validate environment
        if not self.validate_environment():
            return False
        
        # Connect to services
        if not self.connect_to_services():
            return False
        
        # Download and upload data
        if not self.download_and_upload_data():
            return False
        
        print("\nSync completed successfully!")
        print(f"Summary:")
        print(f"   • Source: {self.table_name} table in Neon database")
        print(f"   • Destination: {self.sheets.spreadsheet_name} Google Sheet")
        print(f"   • Records synced: {len(self.df):,}")
        print(f"   • Columns synced: {len(self.df.columns)}")
        
        return True

def main():
    """Main function to run the sync process"""
    sync = OneTimeSyncToSheets()
    
    try:
        success = sync.sync_data()
        if success:
            print("\nOne-time sync process completed successfully!")
        else:
            print("\nSync process failed. Please check the errors above.")
    except KeyboardInterrupt:
        print("\nSync process interrupted by user")
    except Exception as e:
        print(f"\nUnexpected error during sync: {e}")

if __name__ == "__main__":
    main()
