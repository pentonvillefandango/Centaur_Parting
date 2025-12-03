# Centaur Parting - Quick Reference

## 🚀 Quick Start

```bash
# 1. Setup
git clone https://github.com/pentonvillefandango/Centaur_Parting.git
cd Centaur_Parting
python -m venv venv
source venv/bin/activate
pip install numpy astropy photutils scipy

# 2. Test with your data
python test_rig24_fits.py

# 3. Run the watcher
# Process existing files:
python src/monitor/enhanced_watcher.py --process-existing --max-files 10

# Watch for new files only:
python src/monitor/enhanced_watcher.py --continuous

# Process existing then watch:
python src/monitor/enhanced_watcher.py --continuous --process-existing-first

📁 Key Files
src/monitor/enhanced_watcher.py - Main watcher application

src/monitor/enhanced/fits_analyzer.py - Core analysis engine

PROJECT_STATUS.md - Complete project documentation

Centaur_Analysis/ - Analysis output directory

🔑 Key Commands
Command	Purpose	Example
--process-existing	Analyze existing FITS files	--process-existing --max-files 50
--continuous	Watch for NEW files only	--continuous
--process-existing-first	Process existing then watch	--continuous --process-existing-first
--max-files N	Limit processing for testing	--max-files 5
--output DIR	Custom output directory	--output ./my_analysis
--path PATH	Custom watch path	--path /Volumes/MyMount
📊 What It Analyzes
Signal-to-Noise Ratio (SNR)

Background SNR

Faint object SNR (3σ)

Moderate object SNR (10σ)

Sky Brightness

mag/arcsec² calculation

Electrons per pixel/second

Exposure Optimization

Current vs recommended exposure

Optimal sub-exposure length

SHO-specific recommendations

Saturation Detection

Hot pixel identification

Real saturation detection

Severity assessment

⚠️ Stopping the Watcher
Press Ctrl+C to stop gracefully. The watcher will:

Complete current file analysis

Create final summary report

Exit cleanly

📈 Output Files
COMPREHENSIVE_SUMMARY.md - Summary of all analyses

*.json - Detailed JSON analysis reports

*.txt - Human-readable summaries

centaur_watcher.log - Application log

🆘 Need Help?
Check PROJECT_STATUS.md for detailed documentation

Look at log file: Centaur_Analysis/centaur_watcher.log

Test with: python test_rig24_fits.py

🎯 Next Phase Planning
Current system is Phase 1 Complete. Next phase includes:

Web dashboard interface

Database for historical tracking

Visualization and alerts

API for integration


