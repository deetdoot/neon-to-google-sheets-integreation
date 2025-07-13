#!/usr/bin/env python3
"""
Entry point for continuous sync - runs the continuous sync process
"""

import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.sync.continuous_sync import main

if __name__ == "__main__":
    main()
