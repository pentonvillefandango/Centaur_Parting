# Centaur Parting - Astrophotography Dashboard
## Project Status - Last Updated: 2025-12-03 01:30

### 🎯 PROJECT GOAL
Real-time monitoring dashboard for multiple imaging rigs, providing exposure optimization suggestions based on SNR and sky brightness.

### ✅ COMPLETED TODAY
1. **Project foundation** - Directory structure, virtual environment, requirements
2. **Basic GUI framework** - Dear PyGui setup with dark theme
3. **✅ WORKING POLLING WATCHER** - Critical milestone achieved!
   - Monitors `/Volumes/Rig24_Imaging` recursively
   - Detects new FITS files within 2-4 seconds
   - Handles SMB network drive limitations
   - Tested with real files from imaging PC

### 🚧 CURRENT STATE
- **Watcher**: ✅ Fully functional (polling method)
- **Analyzer**: ⚠️ Skeleton created, needs enhancement
- **Database**: ❌ Not started
- **Dashboard**: ⚠️ Basic UI, not connected to backend

### 📋 NEXT PRIORITIES
1. **Enhance FITS analyzer** with lessons from cp-astrowatcher
2. **Create SQLite database schema** (not JSON!)
3. **Connect pipeline**: Watcher → Analyzer → Database
4. **Update dashboard** to show real-time metrics

### 🗄️ DATABASE PLAN (SQLite - NOT JSON)
Tables needed:
- frames (file info, metrics, analysis results)
- sessions (imaging runs per target)
- rigs (equipment profiles)
- suggestions (exposure recommendations)
- thresholds (rig/filter-specific limits)

### 🔧 TECH STACK
- **Python 3.9+** with virtual environment
- **Dear PyGui** for beautiful dashboard
- **astropy, sep, photutils** for FITS analysis
- **SQLite** for data storage
- **watchdog** for file monitoring (polling fallback)

### 📁 PROJECT STRUCTURE
Centaur_Parting/
├── src/
│   ├── dashboard/     # GUI (needs connection to backend)
│   ├── monitor/       # ✅ Polling watcher WORKING
│   ├── analyzer/      # ⚠️ Needs enhancement
│   ├── database/      # ❌ To be built
│   └── utils/
├── config/            # Configuration
├── data/              # SQLite database location
└── logs/              # Application logs

### 💡 KEY INSIGHTS FROM CP-ASTROWATCHER
1. **Primary goal**: SNR + sky brightness for exposure optimization
2. **Avoid JSON**: Use proper SQLite database
3. **Parse filenames**: Rich metadata in naming convention
4. **Multiple metrics**: HFR, star count, eccentricity, background levels
5. **Python astro modules**: astropy, sep, photutils are reliable

### 🔗 GITHUB REPOSITORY
- Main: https://github.com/pentonvillefandango/Centaur_Parting
- Reference: https://github.com/pentonvillefandango/cp-astrowatcher (previous project)

### 🎪 TESTING
- **Watcher test**: python src/monitor/polling_watcher.py
- **GUI test**: python run_dashboard.py
- **Mount path**: /Volumes/Rig24_Imaging

### 🚀 NEXT SESSION STARTING POINT
"Continue Centaur Parting. Polling watcher works. 
Enhance FITS analyzer based on cp-astrowatcher lessons, 
focusing on SNR and sky brightness for exposure optimization."
