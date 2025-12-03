# Centaur Parting - Astrophotography Analysis System

[![Project Status](https://img.shields.io/badge/status-phase%201%20complete-success)](https://github.com/pentonvillefandango/Centaur_Parting)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://python.org)

## Overview

Centaur Parting is an intelligent FITS file analysis system for astrophotography that provides real-time exposure optimization, SNR analysis, and sky brightness monitoring. The system watches for new FITS files and provides actionable recommendations for exposure optimization.

## Features

- **Real-time FITS analysis** as files are captured
- **SNR calculation** for faint object detection
- **Sky brightness measurement** in mag/arcsec²
- **Exposure optimization** recommendations
- **SHO workflow support** with filter-specific advice
- **Saturation detection** with hot pixel identification
- **Batch processing** for historical data analysis

## Quick Start

```bash
# Clone repository
git clone https://github.com/pentonvillefandango/Centaur_Parting.git
cd Centaur_Parting

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Test with sample data
python test_rig24_fits.py

# Run the watcher on your imaging rig
python src/monitor/enhanced_watcher.py --process-existing --max-files 5

Project Structure

Centaur_Parting/
├── src/monitor/                    # Core monitoring system
│   ├── enhanced_polling_watcher.py # Main watcher application
│   ├── enhanced/                   # Enhanced analysis engine
│   │   └── fits_analyzer.py        # Core FITS analysis class
│   └── polling_watcher.py          # Original watcher (legacy)
├── test_rig24_fits.py              # Test script for Rig24 data
├── run_watcher.py                  # Simple entry point
├── requirements.txt                # Python dependencies
├── .gitignore                      # Git ignore rules
├── PROJECT_STATUS.md               # Complete project documentation
├── QUICK_REFERENCE.md             # Quick start guide
└── README.md                       # This file

Usage Examples
Process Existing Files

# Analyze first 50 files
python src/monitor/enhanced_watcher.py --process-existing --max-files 50

# Process all files
python src/monitor/enhanced_watcher.py --process-existing

Monitor for New Files
# Watch for NEW files only (ignore existing)
python src/monitor/enhanced_watcher.py --continuous

# Process existing first, then watch for new
python src/monitor/enhanced_watcher.py --continuous --process-existing-first

Custom Configuration
# Specify custom watch path
python src/monitor/enhanced_watcher.py --path /path/to/fits --continuous

# Use custom output directory
python src/monitor/enhanced_watcher.py --process-existing --output ./my_analysis

Sample Analysis Output
Object: NGC7635
Filter: Ha
Exposure: 300s
Sky Brightness: 19.8 mag/arcsec²
Background SNR: 9.2
Faint Object SNR: 3.0
Saturation: 0.008% (hot pixels)
Recommendation: Exposure time is good: 300.0s
SHO Recommendation: SII/OIII: 180s (0.6x Ha)
Optimal Sub Length: 60s
Noise Regime: Sky-noise limited

Documentation
PROJECT_STATUS.md - Complete project documentation with architecture, implementation details, and future plans

QUICK_REFERENCE.md - Quick start guide and command reference

Development
Dependencies

# Core requirements
numpy>=1.21.0
astropy>=5.0
photutils>=1.5.0
scipy>=1.7.0

# Optional
watchdog>=2.1.0    # Filesystem monitoring
pandas>=1.3.0      # Data analysis
matplotlib>=3.5.0  # Visualization

Running Tests

# Test the analyzer on your Rig24 data
python test_rig24_fits.py

# Run a smoke test
python -c "
import sys
sys.path.append('src/monitor/enhanced')
from fits_analyzer import EnhancedFITSAnalyzer
print('EnhancedFITSAnalyzer imports successfully')
"

## 🌐 Web GUI

Centaur Parting includes a web-based dashboard for monitoring and analysis.

### Start the GUI:
```bash
# Install GUI dependencies
pip install flask waitress

# Run the GUI
python run_gui.py

# For production use:
python run_gui.py --production

Then open your browser to: http://localhost:5000

GUI Features:
Real-time monitoring of FITS file analysis

Dashboard statistics and visualizations

File-by-file analysis with detailed views

Exposure recommendations across all files

SHO workflow support with filter-specific advice

Saturation alerts and sky brightness monitoring


## **What the GUI Provides:**

### **📊 Dashboard Features:**
1. **Real-time Monitoring** - Watch as new FITS files are analyzed
2. **Statistics Overview** - Total analyses, average exposure, sky brightness
3. **File Browser** - Browse and view detailed analysis of each FITS file
4. **Recommendations Panel** - Key exposure recommendations across all files
5. **Controls** - Start/stop watcher, process existing files

### **🔧 Technical Features:**
1. **REST API** - All functionality available via API
2. **Background Processing** - File analysis runs in background threads
3. **Auto-refresh** - Dashboard updates automatically
4. **Responsive Design** - Works on desktop and mobile
5. **Detailed Views** - Click any file for complete analysis details

### **🚀 Quick Start with GUI:**
```bash
# Install
pip install -r requirements.txt

# Run
python run_gui.py

# Open browser to http://localhost:5000



Contributing
Fork the repository

Create a feature branch

Make your changes

Add tests if applicable

Submit a pull request

License
This project is licensed under the MIT License - see the LICENSE file for details.

Acknowledgments
Built for the astrophotography community

Inspired by cp-astrowatcher principles

Thanks to all contributors and testers

Need help? Check the documentation or open an issue on GitHub!




