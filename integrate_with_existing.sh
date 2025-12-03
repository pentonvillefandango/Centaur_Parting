#!/bin/bash
echo "Integrating enhanced FITS analyzer with existing Centaur Parting project..."
echo ""

# Check if enhanced analyzer exists
if [ ! -f "src/monitor/enhanced/fits_analyzer.py" ]; then
    echo "Error: Enhanced analyzer not found at src/monitor/enhanced/fits_analyzer.py"
    exit 1
fi

echo "✅ Enhanced analyzer found"
echo ""

# Create symbolic link or copy to make it easy to use
echo "Setting up for easy access..."
ln -sf src/monitor/enhanced/fits_analyzer.py enhanced_analyzer.py 2>/dev/null || true

echo ""
echo "Available commands:"
echo "  1. Test analyzer:        python test_rig24_fits.py"
echo "  2. Process existing:     python src/monitor/enhanced_watcher.py --process-existing"
echo "  3. Run continuous:       python src/monitor/enhanced_watcher.py --continuous"
echo "  4. Process & monitor:    python src/monitor/enhanced_watcher.py"
echo ""
echo "The enhanced watcher will:"
echo "  • Watch /Volumes/Rig24_Imaging for new FITS files"
echo "  • Analyze SNR and sky brightness"
echo "  • Recommend optimal exposures"
echo "  • Provide SHO-specific recommendations"
echo "  • Save reports to /Volumes/Rig24_Imaging/Centaur_Analysis/"
echo ""

# Quick test
echo "Quick test (first file only)..."
python -c "
import sys
sys.path.append('src/monitor/enhanced')
from fits_analyzer import EnhancedFITSAnalyzer
import glob
files = glob.glob('/Volumes/Rig24_Imaging/**/*.fits', recursive=True)[:1]
if files:
    analyzer = EnhancedFITSAnalyzer(files[0])
    report = analyzer.generate_report()
    print(f'✅ Test successful! Analyzed: {report[\"file_info\"][\"filename\"]}')
    print(f'   Object: {report[\"file_info\"][\"object\"]}')
    print(f'   Filter: {report[\"file_info\"][\"filter\"]}')
    print(f'   Exposure: {report[\"analysis\"][\"current_exposure\"]}s')
    print(f'   Recommended SHO: {report[\"analysis\"][\"sho_recommendation\"][\"recommended_exposure\"]:.0f}s')
else:
    print('❌ No FITS files found')
"
