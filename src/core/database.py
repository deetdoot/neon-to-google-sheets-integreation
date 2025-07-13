#!/usr/bin/env python3
"""
Database Connection Module for Neon PostgreSQL
==============================================

This module provides database connection and query functionality for Neon PostgreSQL.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
import pandas as pd

# Load environment variables from .env file
load_dotenv()

class DatabaseConnection:
    """
    Handles PostgreSQL database connections and operations for Neon database.
    """
    
    def __init__(self):
        """Initialize database connection using environment variables"""
        self.connection_params = {
            'host': os.getenv('PGHOST'),
            'database': os.getenv('PGDATABASE'),
            'user': os.getenv('PGUSER'),
            'password': os.getenv('PGPASSWORD'),
            'port': os.getenv('PGPORT', '5432'),
            'sslmode': 'require'  # Required for most cloud PostgreSQL services
        }
        self.connection = None
    
    def connect(self) -> bool:
        """
        Establish connection to the database
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.connection = psycopg2.connect(**self.connection_params)
            print("Successfully connected to PostgreSQL database")
            return True
        except Exception as e:
            print(f"Error connecting to database: {e}")
            return False
    
    def disconnect(self) -> None:
        """Close database connection"""
        if self.connection:
            self.connection.close()
            print("Database connection closed")
    
    def test_connection(self) -> bool:
        """
        Test the database connection and show basic info
        
        Returns:
            bool: True if connection test successful, False otherwise
        """
        if not self.connect():
            return False
        
        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            
            # Test basic query
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"PostgreSQL Version: {version['version']}")
            
            # Show current database
            cursor.execute("SELECT current_database();")
            db_name = cursor.fetchone()
            print(f"Current Database: {db_name['current_database']}")
            
            # List tables
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()
            
            if tables:
                print(f"Tables in database:")
                for table in tables:
                    print(f"   - {table['table_name']}")
            else:
                print("No tables found in database")
            
            cursor.close()
            return True
            
        except Exception as e:
            print(f"Error testing connection: {e}")
            return False
        finally:
            self.disconnect()
    
    def query_database(self, query: str, params: Optional[tuple] = None) -> Optional[List[Dict[str, Any]]]:
        """
        Execute a custom query on the database
        
        Args:
            query (str): SQL query to execute
            params (tuple, optional): Parameters for the query
            
        Returns:
            List[Dict] or bool or None: Query results for SELECT, True for other operations, None on error
        """
        # Use existing connection or create a new one
        need_to_disconnect = False
        if not self.connection:
            if not self.connect():
                return None
            need_to_disconnect = True
        
        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query, params or ())
            
            # Check if it's a SELECT query or has RETURNING clause
            if query.strip().upper().startswith('SELECT') or 'RETURNING' in query.upper():
                results = cursor.fetchall()
                self.connection.commit()
                cursor.close()
                return [dict(row) for row in results]
            else:
                # For INSERT, UPDATE, DELETE queries without RETURNING
                self.connection.commit()
                cursor.close()
                return True
                
        except Exception as e:
            print(f"Error executing query: {e}")
            self.connection.rollback()
            return None
        finally:
            # Only disconnect if we created the connection in this method
            if need_to_disconnect:
                self.disconnect()
    
    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists in the database
        
        Args:
            table_name (str): Name of the table to check
            
        Returns:
            bool: True if table exists, False otherwise
        """
        query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            );
        """
        
        result = self.query_database(query, (table_name,))
        return result and result[0]['exists'] if result else False
    
    def get_table_info(self, table_name: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get table structure information
        
        Args:
            table_name (str): Name of the table
            
        Returns:
            List[Dict]: Table column information
        """
        query = """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = %s AND table_schema = 'public'
            ORDER BY ordinal_position;
        """
        
        return self.query_database(query, (table_name,))
    
    def get_row_count(self, table_name: str) -> Optional[int]:
        """
        Get the number of rows in a table
        
        Args:
            table_name (str): Name of the table
            
        Returns:
            int: Number of rows, None on error
        """
        query = f'SELECT COUNT(*) as row_count FROM "{table_name}";'
        result = self.query_database(query)
        return result[0]['row_count'] if result else None
    
    def get_table_data(self, table_name: str) -> Optional[pd.DataFrame]:
        """
        Get all data from a table as a pandas DataFrame
        
        Args:
            table_name (str): Name of the table to query
            
        Returns:
            pd.DataFrame: DataFrame containing all table data, None on error
        """
        # Ensure we have a valid connection
        if not self.connection or self.connection.closed:
            if not self.connect():
                return None
        
        try:
            # Query to get all data from the table (with proper quoting for case-sensitive table names)
            query = f'SELECT * FROM "{table_name}" ORDER BY 1;'
            
            cursor = self.connection.cursor()
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            data = cursor.fetchall()
            cursor.close()
            
            if not data:
                print("No data found in table")
                return pd.DataFrame()  # Return empty DataFrame instead of None
                
            # Convert to pandas DataFrame
            df = pd.DataFrame(data, columns=columns)
            
            print(f"Retrieved {len(df)} rows and {len(df.columns)} columns from table '{table_name}'")
            return df
            
        except Exception as e:
            print(f"Error retrieving table data: {e}")
            return None


def main():
    """Main function to test database connection"""
    print("Database Connection Test")
    print("=" * 60)
    
    # Check if environment variables are set
    required_vars = ['PGHOST', 'PGDATABASE', 'PGUSER', 'PGPASSWORD', 'TABLE_NAME']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"Missing environment variables: {', '.join(missing_vars)}")
        print("Make sure your .env file contains all required database credentials")
        return
    
    db = DatabaseConnection()
    table_name = os.getenv('TABLE_NAME')
    
    # Test connection
    print("\n1. Testing database connection...")
    if not db.test_connection():
        print("Connection test failed. Please check your credentials.")
        return
    
    print("\nDatabase connection successful!")
    
    # Connect to the specified table and show summary
    print(f"\n2. Connecting to table '{table_name}'...")
    print("=" * 60)
    
    # Check if table exists
    if not db.table_exists(table_name):
        print(f"Table '{table_name}' not found in the database.")
        print("Please check the TABLE_NAME in your .env file.")
        return
    
    print(f"Successfully connected to table '{table_name}'!")
    
    # Get table info
    table_info = db.get_table_info(table_name)
    row_count = db.get_row_count(table_name)
    
    if table_info:
        # Display table summary
        print(f"\nTABLE SUMMARY:")
        print(f"   Table Name: {table_name}")
        print(f"   Column Count: {len(table_info)}")
        print(f"   Row Count: {row_count:,}" if row_count is not None else "   Row Count: Unable to retrieve")
        
        print(f"\nCOLUMN DETAILS:")
        print(f"   {'#':<3} {'Column Name':<25} {'Data Type':<20} {'Nullable':<10}")
        print(f"   {'-' * 3} {'-' * 25} {'-' * 20} {'-' * 10}")
        
        for i, column in enumerate(table_info, 1):
            nullable = "YES" if column['is_nullable'] == 'YES' else "NO"
            print(f"   {i:<3} {column['column_name']:<25} {column['data_type']:<20} {nullable:<10}")
    
    print(f"\nYou can now use this DatabaseConnection class to:")
    print("   - Execute custom queries with db.query_database()")
    print(f"   - Query the '{table_name}' table")
    print("   - Perform any database operations you need")


if __name__ == "__main__":
    main()
