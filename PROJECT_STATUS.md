# Centaur Parting - Astrophotography Project Status

## 📋 Project Overview
**Centaur Parting** is an astrophotography automation and analysis system that monitors FITS files for exposure optimization, SNR analysis, and sky brightness measurement. The system integrates real-time analysis with historical data tracking to optimize imaging sessions.
**Current Phase:** Phase 1 - Core Analysis Engine Complete ✅
**Next Phase:** Phase 2 - User Interface & Data Persistence

## 🎯 Project Goals
1. **Real-time FITS analysis** for exposure optimization
2. **SNR and sky brightness calculation** for imaging optimization
3. **Automated monitoring** of imaging rig outputs
4. **Historical tracking** of imaging conditions and performance
5. **Actionable recommendations** for astrophotographers

## 🏗️ Architecture

### Core Components

Centaur_Parting/
├── src/monitor/
│ ├── enhanced_polling_watcher.py # Main watcher application
│ ├── enhanced/ # Enhanced analysis engine
│ │ └── fits_analyzer.py # Core FITS analysis class
│ └── polling_watcher.py # Original watcher (legacy)
├── Centaur_Analysis/ # Analysis output directory
│ ├── COMPREHENSIVE_SUMMARY.md # Summary of all analyses
│ ├── centaur_watcher.log # Application log
│ ├── *_centaur_analysis.json # Individual JSON reports
│ └── *_summary.txt # Individual text summaries
├── test_rig24_fits.py # Test script for analysis
└── PROJECT_STATUS.md # This file

#### 1. **Enhanced FITS Analysis** ✅
- **SNR Calculation:** 
  - Background SNR (mean/std)
  - Faint object SNR (3σ above background)
  - Moderate object SNR (10σ above background)
- **Sky Brightness Analysis:**
  - Calculates mag/arcsec² from background levels
  - Accounts for gain, pixel scale, exposure time
  - Handles missing header data gracefully
- **Saturation Detection:**
  - Distinguishes between hot pixels and real saturation
  - Reports percentage of near-saturated pixels
  - Provides severity ratings (NONE, MINOR, MODERATE, HIGH)
- **Exposure Optimization:**
  - Recommends optimal exposure times
  - Calculates exposure factor (recommended/current)
  - Provides SHO-specific recommendations (SII/OIII at 0.6x Ha)
- **Noise Regime Analysis:**
  - Determines if read-noise or sky-noise limited
  - Calculates optimal sub-exposure length

#### 2. **File Watcher System** ✅
- **Mount Monitoring:** Watches `/Volumes/Rig24_Imaging`
- **Smart Processing:** 
  - Ignores existing files by default (when using `--continuous`)
  - Processes existing files on demand (`--process-existing`)
  - Tracks processed files to avoid duplicates
- **Output Management:**
  - Saves analysis locally (mount is read-only)
  - Creates individual JSON reports
  - Generates text summaries for quick viewing
  - Produces comprehensive markdown summary

#### 3. **Command Line Interface** ✅

Process existing files (with limit)
python src/monitor/enhanced_watcher.py --process-existing --max-files 20

Watch for NEW files only (ignore existing)
python src/monitor/enhanced_watcher.py --continuous

Process existing first, then watch
python src/monitor/enhanced_watcher.py --continuous --process-existing-first

Specify custom output directory
python src/monitor/enhanced_watcher.py --process-existing --output ./my_analysis


#### 4. **Analysis Output** ✅
- **Individual Reports:** JSON with complete analysis data
- **Text Summaries:** Human-readable quick summaries
- **Comprehensive Summary:** Markdown report with statistics
- **Logging:** Detailed application log with timestamps

### 📊 Key Features Implemented
1. **Real-time Analysis:** Analyzes FITS files as they appear
2. **Exposure Optimization:** Recommends optimal exposure times
3. **SHO Workflow Support:** Specific recommendations for narrowband filters
4. **Saturation Detection:** Intelligent hot pixel vs. saturation distinction
5. **Sky Conditions Monitoring:** Tracks sky brightness over time
6. **Batch Processing:** Handles large datasets (tested with 580+ files)
7. **Error Resilience:** Continues processing if individual files fail

## 🔧 Technical Implementation Details

### Dependencies
```bash
# Core dependencies
numpy>=1.21.0
astropy>=5.0
photutils>=1.5.0
scipy>=1.7.0

# Optional (for advanced features)
pandas>=1.3.0          # Data analysis
matplotlib>=3.5.0      # Visualization
watchdog>=2.1.0        # Filesystem events (alternative to polling)

Analysis Algorithms
Background Calculation: Sigma-clipped statistics with source masking

SNR Estimation: Multiple methods for robustness

Sky Brightness: Converts ADU to mag/arcsec² using instrument parameters

Optimal Exposure: Balances read noise vs. sky noise

Saturation Analysis: Percentage-based with clustering detection

File Processing Logic
Hashing: Uses file size + modification time to detect changes

Tracking: Maintains set of processed files in memory

Recovery: Can resume processing after interruption

Output: Creates analysis directory with organized files

🎨 Example Output Analysis
From Test Data (NGC7635 Ha frames):
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

Key Insights from Analysis:
300s Ha exposures are working well but slightly longer than optimal

180s recommended for SII/OIII for consistent SHO workflow

Sky brightness ~19.8 mag/arcsec² indicates decent conditions

Minimal saturation (0.008% hot pixels only)

Sky-noise limited - exposures are sufficiently long

📈 Next Phase (Phase 2)
Planned Features
Web Dashboard - Real-time monitoring interface

Database Integration - Store analysis results historically

Visualization - Charts for SNR, sky brightness, exposure trends

Alert System - Notifications for saturation, poor conditions

API Endpoints - Programmatic access to analysis data

Configuration Management - User settings for different rigs

Historical Analysis - Compare sessions over time

Technical Architecture for Phase 2

Centaur_Parting/
├── web/                    # Web interface
│   ├── app.py             # Flask/FastAPI application
│   ├── templates/         # HTML templates
│   ├── static/            # CSS/JS assets
│   └── api/               # REST API endpoints
├── database/              # Data persistence
│   ├── models.py          # SQLAlchemy models
│   ├── schema.sql         # Database schema
│   └── queries.py         # Database operations
├── config/                # Configuration
│   ├── settings.yaml      # User settings
│   └── rig_profiles/      # Camera/telescope profiles
└── analytics/             # Advanced analysis
    ├── trends.py          # Historical trend analysis
    └── predictions.py     # Exposure predictions

Phase 2 Milestones
M1: Basic web dashboard showing current analysis

M2: SQLite database for storing analysis results

M3: Historical charts and trend analysis

M4: User configuration for different imaging setups

M5: Alert system and notifications

M6: API for integration with other tools

🚨 Current Limitations
Known Issues
Read-only Mount: Analysis output must be saved locally

Memory Usage: Large batches (580+ files) use significant RAM

Processing Time: ~2.5 seconds per file (24 minutes for 580 files)

No Historical Tracking: Current implementation doesn't store results long-term

Basic UI: Command-line only, no graphical interface

Dependencies to Monitor
Astropy/Photutils: Version compatibility with FITS formats

NumPy/SciPy: Memory usage with large images

Filesystem Access: Mount stability and permissions

🛠️ Development & Testing
Setup Instructions
# 1. Clone repository
git clone https://github.com/pentonvillefandango/Centaur_Parting.git
cd Centaur_Parting

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install numpy astropy photutils scipy

# 4. Test with sample data
python test_rig24_fits.py

# 5. Run the watcher
python src/monitor/enhanced_watcher.py --process-existing --max-files 5

Testing Strategy
Unit Tests: Individual analyzer functions

Integration Tests: Full file processing pipeline

Performance Tests: Large batch processing

Real-world Testing: Actual imaging rig output

Debugging Tips

# Check log file
tail -f Centaur_Analysis/centaur_watcher.log

# Test individual file analysis
python -c "
import sys
sys.path.append('src/monitor/enhanced')
from fits_analyzer import EnhancedFITSAnalyzer
analyzer = EnhancedFITSAnalyzer('test.fits')
print(analyzer.generate_report()['recommendations'])
"

# Monitor memory usage
ps aux | grep enhanced_watcher
🔮 Future Vision
Long-term Goals
Intelligent Exposure Planning: AI-driven exposure recommendations

Weather Integration: Combine with weather/seeing forecasts

Multi-rig Support: Monitor multiple imaging setups

Community Features: Share successful exposure settings

Mobile App: Remote monitoring and alerts

Integration Opportunities
Sequence Generators: NINA, Sequence Generator Pro

Plate Solvers: Astrometry.net, ASTAP

Weather Stations: Weather monitoring APIs

Observatory Control: ASCOM, INDI

Cloud Services: AWS/Azure for distributed analysis

📞 Support & Contact
Getting Help
Issues: GitHub Issues for bug reports

Documentation: This file and code comments

Examples: Test scripts and sample output

Contributing
Code Style: PEP 8 compliant

Testing: Include tests for new features

Documentation: Update this file for major changes

Last Updated: 2025-12-03
Current Version: 1.0
Status: Phase 1 Complete, Ready for Phase 2 Planning
Maintainer: Project Team
Repository: https://github.com/pentonvillefandango/Centaur_Parting


