#!/usr/bin/env python3
"""
Neon to Google Sheets Continuous Sync Script
===========================================

This script connects to Neon PostgreSQL database, downloads table data,
and uploads it to Google Sheets with continuous sync capability.
"""

import os
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime
import time
import signal
import sys

# Import from our modular structure
from src.core.database import DatabaseConnection
from src.core.sheets import GoogleSheetsConnection

# Load environment variables
load_dotenv()

class NeonToSheetsSync:
    def __init__(self):
        """Initialize the sync class with database and sheets connections"""
        self.db = DatabaseConnection()
        self.sheets = GoogleSheetsConnection()
        self.table_name = os.getenv('TABLE_NAME')
        self.sync_interval = int(os.getenv('SYNC_INTERVAL_MINUTES', '2')) * 60  # Convert minutes to seconds
        self.df = None
        self.is_running = True
        
        # Set up signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\nReceived shutdown signal ({signum}). Stopping sync...")
        self.is_running = False
    
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
        
        # Connect to Google Sheets
        if not self.sheets.connect():
            print("Failed to connect to Google Sheets")
            return False
        
        # Setup worksheets
        if not self.sheets.setup_worksheets(self.table_name):
            print("Failed to setup Google Sheets worksheets")
            return False
        
        print(f"Successfully connected to all services")
        print(f"Spreadsheet URL: {self.sheets.get_spreadsheet_url()}")
        return True
    
    def perform_sync_cycle(self):
        """Perform a single sync cycle (download data and update sheets)"""
        try:
            # Download data from database
            print(f"Downloading data from table '{self.table_name}'...")
            self.df = self.db.get_table_data(self.table_name)
            
            if self.df is None or len(self.df) == 0:
                print("No data found in table")
                return False
            
            print(f"Downloaded {len(self.df)} rows and {len(self.df.columns)} columns")
            
            # Update Google Sheets
            print("Updating Google Sheets...")
            if not self.sheets.update_data_worksheet(self.df, f"{self.table_name}_data"):
                print("Failed to update data worksheet")
                return False
            
            # Update metadata
            metadata = {
                "Last Sync Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Source Table": self.table_name,
                "Total Rows": len(self.df),
                "Total Columns": len(self.df.columns),
                "Data Worksheet": f"{self.table_name}_data",
                "Sync Interval": f"{self.sync_interval/60:.1f} minutes",
                "Status": "Running"
            }
            
            if not self.sheets.update_metadata_worksheet(metadata):
                print("Failed to update metadata worksheet")
                return False
            
            current_time = datetime.now().strftime("%H:%M:%S")
            print(f"[{current_time}] Successfully updated {len(self.df)} rows in Google Sheets")
            return True
            
        except Exception as e:
            print(f"Error during sync cycle: {e}")
            return False
    
    def start_continuous_sync(self):
        """Start continuous sync process with the specified interval"""
        print("Starting continuous sync process...")
        print(f"Sync interval: {self.sync_interval/60:.1f} minutes")
        print("Press Ctrl+C to stop the sync process")
        print("=" * 60)
        
        # Validate environment
        if not self.validate_environment():
            return False
        
        # Initial setup - Connect to services
        if not self.connect_to_services():
            return False
        
        # Initial data sync
        print("\nPerforming initial sync...")
        if not self.perform_sync_cycle():
            print("Initial sync failed")
            return False
        
        print(f"\nInitial sync completed! Starting continuous sync every {self.sync_interval/60:.1f} minutes...")
        
        # Continuous sync loop
        sync_count = 1
        
        while self.is_running:
            try:
                # Wait for the specified interval
                for i in range(self.sync_interval):
                    if not self.is_running:
                        break
                    time.sleep(1)
                
                if not self.is_running:
                    break
                
                # Perform sync
                sync_count += 1
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"\n[{current_time}] Starting sync #{sync_count}...")
                
                if self.perform_sync_cycle():
                    print(f"Sync #{sync_count} completed successfully")
                else:
                    print(f"Sync #{sync_count} failed")
                    
            except Exception as e:
                print(f"Error during sync cycle: {e}")
                time.sleep(5)  # Wait a bit before retrying
        
        # Cleanup
        print("\nShutting down sync process...")
        if self.db.connection:
            self.db.disconnect()
        
        # Update metadata to show stopped status
        try:
            final_metadata = {
                "Last Sync Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Source Table": self.table_name,
                "Total Syncs Completed": sync_count,
                "Status": "Stopped"
            }
            self.sheets.update_metadata_worksheet(final_metadata)
        except:
            pass  # Ignore errors during cleanup
            
        print("Sync process stopped gracefully")
        return True

def main():
    """Main function to run the continuous sync process"""
    sync = NeonToSheetsSync()
    
    print("Neon to Google Sheets Continuous Sync")
    print("=" * 50)
    print(f"Table: {sync.table_name}")
    print(f"Spreadsheet: {sync.sheets.spreadsheet_name}")
    print(f"Sync Interval: {sync.sync_interval/60:.1f} minutes")
    print("=" * 50)
    
    try:
        success = sync.start_continuous_sync()
        if success:
            print("\nContinuous sync process completed!")
        else:
            print("\nContinuous sync process failed. Please check the errors above.")
    except KeyboardInterrupt:
        print("\nSync process interrupted by user")
        sync.is_running = False
    except Exception as e:
        print(f"\nUnexpected error during sync: {e}")
        sync.is_running = False

if __name__ == "__main__":
    main()
