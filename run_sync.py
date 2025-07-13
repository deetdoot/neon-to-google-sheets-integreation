#!/usr/bin/env python3
"""
Interactive runner script for Neon to Google Sheets sync
"""

import os
import sys
from dotenv import load_dotenv

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.sync.continuous_sync import NeonToSheetsSync
from src.sync.one_time_sync import OneTimeSyncToSheets

# Load environment variables
load_dotenv()

def show_configuration():
    """Display current configuration"""
    table_name = os.getenv('TABLE_NAME', 'Not set')
    sync_interval = os.getenv('SYNC_INTERVAL_MINUTES', '2')
    spreadsheet_name = os.getenv('SPREADSHEET_NAME', 'Auto-generated')
    
    print(f"Current Configuration:")
    print(f"  Table: {table_name}")
    print(f"  Spreadsheet: {spreadsheet_name}")
    print(f"  Sync Interval: {sync_interval} minutes")

def main():
    """Main function for interactive sync runner"""
    print("Neon to Google Sheets Data Sync")
    print("This script will sync data from your Neon database to Google Sheets")
    print("-" * 60)
    
    # Show current configuration
    show_configuration()
    print("-" * 60)
    
    # Ask user for sync type
    print("Choose sync type:")
    print("1. Continuous sync (runs every X minutes)")
    print("2. One-time sync (sync once and exit)")
    
    while True:
        choice = input("Enter your choice (1 or 2): ").strip()
        
        if choice == '1':
            print("\nStarting continuous sync...")
            sync = NeonToSheetsSync()
            success = sync.start_continuous_sync()
            break
        elif choice == '2':
            print("\nStarting one-time sync...")
            sync = OneTimeSyncToSheets()
            success = sync.sync_data()
            break
        else:
            print("Invalid choice. Please enter 1 or 2.")
    
    print("\nSync process finished.")

if __name__ == "__main__":
    main()
