#!/usr/bin/env python3
"""
Wrapper script to run the trading environment with proper imports.
This avoids relative import issues by ensuring the module is run correctly.
"""

import sys
import os

# Add the current directory to Python path to ensure imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Now import and run the main function
if __name__ == "__main__":
    from main import main
    sys.exit(main())
