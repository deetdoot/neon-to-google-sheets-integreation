#!/usr/bin/env python3
"""
Google Sheets Connection Module
==============================

This module provides Google Sheets API connectivity and operations.
"""

import os
import gspread
from dotenv import load_dotenv
from typing import Optional, Dict, Any, List
from datetime import datetime
import pandas as pd

# Load environment variables
load_dotenv()

class GoogleSheetsConnection:
    """
    Handles Google Sheets API connections and operations.
    """
    
    def __init__(self):
        """Initialize Google Sheets connection using environment variables"""
        self.spreadsheet_name = os.getenv("SPREADSHEET_NAME") or os.getenv("TABLE_NAME") or "neon_to_google_sheets"
        self.gc = None
        self.spreadsheet = None
        self.credentials = self._build_credentials()
    
    def _build_credentials(self) -> Dict[str, Any]:
        """
        Build credentials dictionary from environment variables
        
        Returns:
            Dict: OAuth credentials dictionary
        """
        return {
            "installed": {
                "client_id": os.getenv("CLIENT_ID"),
                "project_id": os.getenv("PROJECT_ID"),
                "auth_uri": os.getenv("AUTH_URI", "https://accounts.google.com/o/oauth2/auth"),
                "token_uri": os.getenv("TOKEN_URI", "https://oauth2.googleapis.com/token"),
                "auth_provider_x509_cert_url": os.getenv("AUTH_PROVIDER_X509_CERT_URL", 
                                                        "https://www.googleapis.com/oauth2/v1/certs"),
                "client_secret": os.getenv("CLIENT_SECRET"),
                "redirect_uris": [os.getenv("REDIRECT_URI", "http://localhost")]
            }
        }
    
    def connect(self) -> bool:
        """
        Establish connection to Google Sheets API
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Authenticate and get client
            self.gc, authorized_user = gspread.oauth_from_dict(self.credentials)
            
            # Open or create spreadsheet
            try:
                self.spreadsheet = self.gc.open(self.spreadsheet_name)
                print(f"Connected to existing spreadsheet '{self.spreadsheet_name}'")
            except gspread.SpreadsheetNotFound:
                self.spreadsheet = self.gc.create(self.spreadsheet_name)
                print(f"Created new spreadsheet '{self.spreadsheet_name}'")
            
            return True
            
        except Exception as e:
            print(f"Error connecting to Google Sheets: {e}")
            return False
    
    def get_or_create_worksheet(self, worksheet_name: str, rows: int = 1000, cols: int = 50) -> Optional[gspread.Worksheet]:
        """
        Get existing worksheet or create new one
        
        Args:
            worksheet_name (str): Name of the worksheet
            rows (int): Number of rows for new worksheet
            cols (int): Number of columns for new worksheet
            
        Returns:
            gspread.Worksheet: Worksheet object or None on error
        """
        try:
            worksheet = self.spreadsheet.worksheet(worksheet_name)
            print(f"Using existing worksheet '{worksheet_name}'")
            return worksheet
        except gspread.WorksheetNotFound:
            worksheet = self.spreadsheet.add_worksheet(title=worksheet_name, rows=rows, cols=cols)
            print(f"Created new worksheet '{worksheet_name}'")
            return worksheet
        except Exception as e:
            print(f"Error accessing worksheet '{worksheet_name}': {e}")
            return None
    
    def update_worksheet_data(self, worksheet: gspread.Worksheet, data: List[List[str]]) -> bool:
        """
        Update worksheet with data
        
        Args:
            worksheet (gspread.Worksheet): Worksheet to update
            data (List[List[str]]): Data to upload
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            worksheet.clear()
            worksheet.update(range_name='A1', values=data)
            return True
        except Exception as e:
            print(f"Error updating worksheet data: {e}")
            return False
    
    def prepare_dataframe_for_upload(self, df: pd.DataFrame) -> List[List[str]]:
        """
        Prepare pandas DataFrame for Google Sheets upload
        
        Args:
            df (pd.DataFrame): DataFrame to prepare
            
        Returns:
            List[List[str]]: Cleaned data ready for upload
        """
        # Convert DataFrame to list of lists (including headers)
        data_to_upload = [df.columns.tolist()] + df.values.tolist()
        
        # Handle potential data type issues (convert to strings)
        cleaned_data = []
        for row in data_to_upload:
            cleaned_row = []
            for cell in row:
                if pd.isna(cell):
                    cleaned_row.append("")
                elif isinstance(cell, (pd.Timestamp, datetime)):
                    cleaned_row.append(cell.strftime("%Y-%m-%d %H:%M:%S"))
                else:
                    cleaned_row.append(str(cell))
            cleaned_data.append(cleaned_row)
        
        return cleaned_data
    
    def create_metadata_sheet(self, table_name: str, df: pd.DataFrame, sync_interval: Optional[float] = None) -> bool:
        """
        Create or update metadata sheet with sync information
        
        Args:
            table_name (str): Source table name
            df (pd.DataFrame): Data that was synced
            sync_interval (float, optional): Sync interval in minutes
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            metadata_sheet = self.get_or_create_worksheet("Sync_Metadata", rows=10, cols=3)
            if not metadata_sheet:
                return False
            
            # Prepare metadata information
            sync_info = [
                ["Attribute", "Value"],
                ["Last Sync Time", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                ["Source Table", table_name],
                ["Total Rows", len(df)],
                ["Total Columns", len(df.columns)],
                ["Data Worksheet", f"{table_name}_data"],
                ["Spreadsheet URL", self.spreadsheet.url]
            ]
            
            # Add sync interval if provided
            if sync_interval:
                sync_info.append(["Sync Interval", f"{sync_interval:.1f} minutes"])
                sync_info.append(["Status", "Running"])
            else:
                sync_info.append(["Sync Type", "One-time"])
            
            return self.update_worksheet_data(metadata_sheet, sync_info)
            
        except Exception as e:
            print(f"Error creating metadata sheet: {e}")
            return False
    
    def get_spreadsheet_url(self) -> Optional[str]:
        """
        Get the URL of the current spreadsheet
        
        Returns:
            str: Spreadsheet URL or None if not connected
        """
        return self.spreadsheet.url if self.spreadsheet else None
    
    def setup_worksheets(self, table_name: str) -> bool:
        """
        Setup required worksheets for the sync operation
        
        Args:
            table_name (str): Name of the table being synced
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create data worksheet
            data_worksheet_name = f"{table_name}_data"
            data_worksheet = self.get_or_create_worksheet(data_worksheet_name, rows=1000, cols=50)
            if not data_worksheet:
                return False
            
            # Create metadata worksheet
            metadata_worksheet = self.get_or_create_worksheet("Sync_Metadata", rows=10, cols=3)
            if not metadata_worksheet:
                return False
            
            return True
            
        except Exception as e:
            print(f"Error setting up worksheets: {e}")
            return False
    
    def update_data_worksheet(self, df: pd.DataFrame, worksheet_name: str) -> bool:
        """
        Update data worksheet with DataFrame content
        
        Args:
            df (pd.DataFrame): DataFrame to upload
            worksheet_name (str): Name of the worksheet to update
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            worksheet = self.get_or_create_worksheet(worksheet_name, 
                                                   rows=max(len(df)+10, 100), 
                                                   cols=max(len(df.columns)+5, 20))
            if not worksheet:
                return False
            
            # Prepare data for upload
            cleaned_data = self.prepare_dataframe_for_upload(df)
            
            # Update worksheet
            return self.update_worksheet_data(worksheet, cleaned_data)
            
        except Exception as e:
            print(f"Error updating data worksheet: {e}")
            return False
    
    def update_metadata_worksheet(self, metadata: Dict[str, Any]) -> bool:
        """
        Update metadata worksheet with sync information
        
        Args:
            metadata (Dict): Metadata dictionary
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            metadata_sheet = self.get_or_create_worksheet("Sync_Metadata", rows=10, cols=3)
            if not metadata_sheet:
                return False
            
            # Convert metadata dict to list format
            sync_info = [["Attribute", "Value"]]
            for key, value in metadata.items():
                sync_info.append([key, str(value)])
            
            return self.update_worksheet_data(metadata_sheet, sync_info)
            
        except Exception as e:
            print(f"Error updating metadata worksheet: {e}")
            return False


def main():
    """Main function to test Google Sheets connection"""
    print("Google Sheets Connection Test")
    print("=" * 40)
    
    # Check if environment variables are set
    required_vars = ['CLIENT_ID', 'CLIENT_SECRET', 'PROJECT_ID']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"Missing environment variables: {', '.join(missing_vars)}")
        print("Make sure your .env file contains all required Google OAuth credentials")
        return
    
    sheets = GoogleSheetsConnection()
    
    print(f"Testing connection to spreadsheet: '{sheets.spreadsheet_name}'")
    
    if sheets.connect():
        print("Google Sheets connection successful!")
        print(f"Spreadsheet URL: {sheets.get_spreadsheet_url()}")
        
        # Test creating a simple worksheet
        test_worksheet = sheets.get_or_create_worksheet("Test_Connection")
        if test_worksheet:
            test_data = [
                ["Test", "Connection", "Status"],
                ["Google Sheets", "API", "Working"],
                ["Timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Success"]
            ]
            
            if sheets.update_worksheet_data(test_worksheet, test_data):
                print("Test data uploaded successfully!")
            else:
                print("Failed to upload test data")
        else:
            print("Failed to create test worksheet")
    else:
        print("Google Sheets connection failed!")


if __name__ == "__main__":
    main()
