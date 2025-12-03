#!/usr/bin/env python3
"""
Test the FITS analyzer
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from analyzer.fits_analyzer import FitsAnalyzer, test_analyzer

if __name__ == "__main__":
    print("Testing FITS Analyzer...")
    try:
        analyzer = FitsAnalyzer()
        print("✅ FITS Analyzer created successfully!")
        print("\nReady to analyze your FITS files.")
        print("\nTo test with a real FITS file, run:")
        print("python -c \"from analyzer.fits_analyzer import FitsAnalyzer; ")
        print("a = FitsAnalyzer(); ")
        print("result = a.analyze_file('path/to/your/file.fits'); ")
        print("print(f'HFR: {result[\"metrics\"].get(\"hfr\", 0):.2f}'); ")
        print("print(f'Stars: {result[\"metrics\"].get(\"star_count\", 0)}')\"")
        
    except ImportError as e:
        print(f"❌ Error: {e}")
        print("\nInstall missing packages:")
        print("pip install astropy sep scipy")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
