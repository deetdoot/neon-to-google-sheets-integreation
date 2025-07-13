#!/usr/bin/env python3
"""
Entry point for one-time sync - runs a single sync operation
"""

import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.sync.one_time_sync import main

if __name__ == "__main__":
    main()
