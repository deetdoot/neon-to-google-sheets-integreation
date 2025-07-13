#!/usr/bin/env python3
"""
Database Connection Script
==================================================

This script connects to the PostgreSQL database using environment variables
and provides basic database operations for testing and management.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import json
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

class DatabaseConnection:
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
    
    def connect(self):
        """Establish connection to the database"""
        try:
            self.connection = psycopg2.connect(**self.connection_params)
            print("Successfully connected to PostgreSQL database")
            return True
        except Exception as e:
            print(f"Error connecting to database: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            print("Database connection closed")
    
    def test_connection(self):
        """Test the database connection and show basic info"""
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
    
    def query_database(self, query, params=None):
        """Execute a custom query on the database"""
        if not self.connect():
            return None
        
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
            self.disconnect()

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
    
    # Get table structure and column count
    table_structure_query = """
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns 
        WHERE table_name = %s AND table_schema = 'public'
        ORDER BY ordinal_position;
    """
    
    table_info = db.query_database(table_structure_query, (table_name,))
    
    if table_info:
        print(f"Successfully connected to table '{table_name}'!")
        
        # Display table summary
        print(f"\nTABLE SUMMARY:")
        print(f"   Table Name: {table_name}")
        print(f"   Column Count: {len(table_info)}")
        
        # Get row count
        row_count_query = f'SELECT COUNT(*) as row_count FROM "{table_name}";'
        row_count_result = db.query_database(row_count_query)
        
        if row_count_result:
            row_count = row_count_result[0]['row_count']
            print(f"   Row Count: {row_count:,}")
        else:
            print("   Row Count: Unable to retrieve")
        
        print(f"\nCOLUMN DETAILS:")
        print(f"   {'#':<3} {'Column Name':<25} {'Data Type':<20} {'Nullable':<10}")
        print(f"   {'-' * 3} {'-' * 25} {'-' * 20} {'-' * 10}")
        
        for i, column in enumerate(table_info, 1):
            nullable = "YES" if column['is_nullable'] == 'YES' else "NO"
            print(f"   {i:<3} {column['column_name']:<25} {column['data_type']:<20} {nullable:<10}")
            
    else:
        print(f"Table '{table_name}' not found in the database.")
        print("Please check the TABLE_NAME in your .env file.")
        return
    
    print(f"\nYou can now use this DatabaseConnection class to:")
    print("   - Execute custom queries with db.query_database()")
    print(f"   - Query the '{table_name}' table")
    print("   - Perform any database operations you need")

if __name__ == "__main__":
    main()
