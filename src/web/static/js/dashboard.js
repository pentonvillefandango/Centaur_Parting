// Centaur Parting Dashboard JavaScript

let currentPage = 1;
const perPage = 20;
let autoRefreshInterval = null;
let watcherRunning = false;
let refreshInterval = 10000; // 10 seconds default
let countdownInterval = null;
let countdownValue = 10;
let lastDataUpdate = null;

// New state for our features
let currentView = localStorage.getItem('preferred-view') || 'compact';
let currentFilters = {
    rig: 'all',
    filterType: 'all',
    status: 'all'
};
let allAnalysesData = []; // Store all loaded analyses for filtering

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard initialized');
    
    // Initialize components
    setupEventListeners();
    setupViewToggle();
    setupFilterControls();
    loadAnalyses();
    loadWatcherStatus();
    loadRigSummary();
    
    // Start with auto-refresh if toggle is on
    const autoRefreshToggle = document.getElementById('auto-refresh-toggle');
    if (autoRefreshToggle && autoRefreshToggle.checked) {
        startAutoRefresh();
    }
    
    // Initialize refresh rate display
    updateRefreshRateDisplay();
    
    console.log('Dashboard ready');
});

function setupEventListeners() {
    // Start/Stop watcher buttons
    const startBtn = document.getElementById('start-watcher-btn');
    const stopBtn = document.getElementById('stop-watcher-btn');
    const refreshBtn = document.getElementById('refresh-now-btn');
    
    if (startBtn) startBtn.addEventListener('click', startWatcher);
    if (stopBtn) stopBtn.addEventListener('click', stopWatcher);
    if (refreshBtn) refreshBtn.addEventListener('click', refreshNow);
    
    // Process existing files button
    const processBtn = document.getElementById('process-existing-btn');
    if (processBtn) {
        processBtn.addEventListener('click', function() {
            const count = prompt('How many existing files to process?', '10');
            if (count && !isNaN(count)) {
                processExistingFiles(parseInt(count));
            }
        });
    }
    
    // Auto-refresh toggle
    const autoRefreshToggle = document.getElementById('auto-refresh-toggle');
    if (autoRefreshToggle) {
        autoRefreshToggle.addEventListener('change', function() {
            if (this.checked) {
                startAutoRefresh();
            } else {
                stopAutoRefresh();
            }
        });
    }
    
    // Refresh rate selector
    const refreshRateSelect = document.getElementById('refresh-rate-select');
    if (refreshRateSelect) {
        refreshRateSelect.addEventListener('change', function() {
            refreshInterval = parseInt(this.value);
            updateRefreshRateDisplay();
            
            // Restart auto-refresh with new interval if it's running
            if (autoRefreshToggle && autoRefreshToggle.checked) {
                stopAutoRefresh();
                startAutoRefresh();
            }
        });
    }
    
    // Export analysis button
    const exportBtn = document.getElementById('export-analysis-btn');
    if (exportBtn) {
        exportBtn.addEventListener('click', exportCurrentAnalysis);
    }
    
    // Theme toggle
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const currentTheme = document.documentElement.getAttribute('data-bs-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            document.documentElement.setAttribute('data-bs-theme', newTheme);
            localStorage.setItem('theme', newTheme);
        });
    }
}

function setupViewToggle() {
    // View toggle buttons
    document.querySelectorAll('.view-toggle-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            // Remove active class from all view toggle buttons
            document.querySelectorAll('.view-toggle-btn').forEach(b => {
                b.classList.remove('active');
            });
            // Add active class to clicked button
            this.classList.add('active');
            
            // Get the view type
            const viewType = this.getAttribute('data-view');
            currentView = viewType;
            localStorage.setItem('preferred-view', viewType);
            
            // Show/hide tables
            const compactTable = document.getElementById('compact-view-table');
            const detailedTable = document.getElementById('detailed-view-table');
            
            if (viewType === 'compact') {
                if (compactTable) compactTable.classList.remove('d-none');
                if (detailedTable) detailedTable.classList.add('d-none');
            } else {
                if (compactTable) compactTable.classList.add('d-none');
                if (detailedTable) detailedTable.classList.remove('d-none');
            }
            
            // Re-render the current view
            renderCurrentView();
        });
    });
    
    // Load preferred view from localStorage
    const preferredView = localStorage.getItem('preferred-view') || 'compact';
    const viewBtn = document.querySelector(`.view-toggle-btn[data-view="${preferredView}"]`);
    if (viewBtn) {
        viewBtn.click();
    }
}

function setupFilterControls() {
    // Filter buttons - Rig
    document.querySelectorAll('[data-filter-rig]').forEach(btn => {
        btn.addEventListener('click', function() {
            // Remove active class from all rig filter buttons
            document.querySelectorAll('[data-filter-rig]').forEach(b => {
                b.classList.remove('active');
            });
            // Add active class to clicked button
            this.classList.add('active');
            
            // Update filter and apply
            currentFilters.rig = this.getAttribute('data-filter-rig');
            applyFilters();
        });
    });
    
    // Filter buttons - Filter Type
    document.querySelectorAll('[data-filter-type]').forEach(btn => {
        btn.addEventListener('click', function() {
            // Remove active class from all type filter buttons
            document.querySelectorAll('[data-filter-type]').forEach(b => {
                b.classList.remove('active');
            });
            // Add active class to clicked button
            this.classList.add('active');
            
            // Update filter and apply
            currentFilters.filterType = this.getAttribute('data-filter-type');
            applyFilters();
        });
    });
    
    // Filter buttons - Status
    document.querySelectorAll('[data-filter-status]').forEach(btn => {
        btn.addEventListener('click', function() {
            // Remove active class from all status filter buttons
            document.querySelectorAll('[data-filter-status]').forEach(b => {
                b.classList.remove('active');
            });
            // Add active class to clicked button
            this.classList.add('active');
            
            // Update filter and apply
            currentFilters.status = this.getAttribute('data-filter-status');
            applyFilters();
        });
    });
}

function startAutoRefresh() {
    stopAutoRefresh(); // Clear any existing
    
    console.log(`Starting auto-refresh every ${refreshInterval/1000}s`);
    
    // Update UI
    const refreshRateText = document.getElementById('refresh-rate-text');
    if (refreshRateText) {
        refreshRateText.textContent = `Rate: ${refreshInterval/1000}s`;
    }
    
    // Start countdown
    startCountdown();
    
    // Initial refresh
    refreshNow();
    
    // Set up periodic refresh
    if (refreshInterval > 0) {
        autoRefreshInterval = setInterval(() => {
            refreshNow();
        }, refreshInterval);
    }
}

function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
    
    if (countdownInterval) {
        clearInterval(countdownInterval);
        countdownInterval = null;
    }
    
    // Reset progress bar
    const refreshProgress = document.getElementById('refresh-progress');
    if (refreshProgress) {
        refreshProgress.style.width = '0%';
    }
    
    const nextRefreshText = document.getElementById('next-refresh-text');
    if (nextRefreshText) {
        nextRefreshText.textContent = 'Auto-refresh stopped';
    }
    
    const refreshRateText = document.getElementById('refresh-rate-text');
    if (refreshRateText) {
        refreshRateText.textContent = 'Rate: Off';
    }
}

function startCountdown() {
    if (countdownInterval) {
        clearInterval(countdownInterval);
    }
    
    countdownValue = refreshInterval / 1000;
    
    countdownInterval = setInterval(() => {
        countdownValue--;
        
        if (countdownValue <= 0) {
            countdownValue = refreshInterval / 1000;
        }
        
        // Update progress bar (smooth animation)
        const progressPercent = 100 - ((countdownValue / (refreshInterval / 1000)) * 100);
        const refreshProgress = document.getElementById('refresh-progress');
        if (refreshProgress) {
            refreshProgress.style.width = `${progressPercent}%`;
        }
        
        // Update text
        const nextRefreshText = document.getElementById('next-refresh-text');
        if (nextRefreshText) {
            nextRefreshText.textContent = `Next refresh in: ${countdownValue}s`;
        }
            
    }, 1000);
}

function updateRefreshRateDisplay() {
    const rateText = refreshInterval === 0 ? 'Off' : `${refreshInterval/1000}s`;
    const refreshRateText = document.getElementById('refresh-rate-text');
    if (refreshRateText) {
        refreshRateText.textContent = `Rate: ${rateText}`;
    }
}

function refreshNow() {
    console.log('Manual refresh triggered');
    loadAnalyses(currentPage);
    loadWatcherStatus();
    loadRigSummary();
}

function loadAnalyses(page = 1) {
    currentPage = page;
    
    fetch(`/api/analyses?page=${page}&per_page=${perPage}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log(`Loaded ${data.analyses?.length || 0} analyses`);
            
            // Store all analyses for filtering
            allAnalysesData = data.analyses || [];
            
            // Apply current filters
            applyFilters();
            
            updatePagination(data);
            updateLastUpdateTime();
            
            // Update displayed files count
            const countElement = document.getElementById('displayed-files-count');
            if (countElement) {
                const filteredCount = data.analyses?.length || 0;
                countElement.textContent = `${filteredCount} files`;
            }
        })
        .catch(error => {
            console.error('Error loading analyses:', error);
            showError('Failed to load analyses: ' + error.message);
        });
}

function applyFilters() {
    // Update filter display
    updateFilterDisplay();
    
    // Filter the data
    const filteredData = filterData(allAnalysesData, currentFilters);
    
    // Update displayed count
    const displayedFilesCount = document.getElementById('displayed-files-count');
    if (displayedFilesCount) {
        displayedFilesCount.textContent = `${filteredData.length} files`;
    }
    
    // Re-render the current view
    renderCurrentView();
}

function filterData(data, filters) {
    if (!data || !Array.isArray(data)) return [];
    
    return data.filter(item => {
        const fileInfo = item.file_info || {};
        const analysisData = item.analysis || {};
        const sat = analysisData.saturation_analysis || {};
        
        // Extract values for filtering
        const rig = fileInfo.rig || 'Unknown';
        const filterType = fileInfo.filter || 'Unknown';
        let status = 'Good'; // Default
        
        // Determine status from saturation analysis
        if (sat.severity === 'CRITICAL') {
            status = 'Critical';
        } else if (sat.severity === 'MODERATE') {
            status = 'Moderate';
        }
        
        // Apply filters
        if (filters.rig !== 'all' && rig !== filters.rig) {
            return false;
        }
        
        if (filters.filterType !== 'all' && filterType !== filters.filterType) {
            return false;
        }
        
        if (filters.status !== 'all' && status !== filters.status) {
            return false;
        }
        
        return true;
    });
}

function updateFilterDisplay() {
    const displayElement = document.getElementById('current-filter-display');
    if (!displayElement) return;
    
    let filters = [];
    
    if (currentFilters.rig !== 'all') filters.push(`${currentFilters.rig}`);
    if (currentFilters.filterType !== 'all') filters.push(`${currentFilters.filterType} filter`);
    if (currentFilters.status !== 'all') filters.push(`${currentFilters.status} status`);
    
    if (filters.length === 0) {
        displayElement.textContent = 'All files';
    } else {
        displayElement.textContent = filters.join(', ');
    }
}

function renderCurrentView() {
    // Get filtered data
    const filteredData = filterData(allAnalysesData, currentFilters);
    
    if (currentView === 'compact') {
        renderCompactView(filteredData);
    } else {
        renderDetailedView(filteredData);
    }
}

function renderCompactView(analyses) {
    const tableBody = document.getElementById('compact-analyses-table');
    if (!tableBody) return;
    
    if (!analyses || analyses.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="14" class="text-center py-5">
                    <div class="mb-3">
                        <i class="bi bi-inbox" style="font-size: 3rem; opacity: 0.3;"></i>
                    </div>
                    <h5 class="text-muted">No matching analyses</h5>
                    <p class="text-muted mb-0">
                        Try changing your filter settings
                    </p>
                </td>
            </tr>
        `;
        return;
    }
    
    let html = '';
    analyses.forEach((analysis) => {
        html += createCompactRow(analysis);
    });
    
    tableBody.innerHTML = html;
    attachViewButtonListeners();
}

function renderDetailedView(analyses) {
    const tableBody = document.getElementById('detailed-analyses-table');
    if (!tableBody) return;
    
    if (!analyses || analyses.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="2" class="text-center py-5">
                    <div class="mb-3">
                        <i class="bi bi-inbox" style="font-size: 3rem; opacity: 0.3;"></i>
                    </div>
                    <h5 class="text-muted">No matching analyses</h5>
                    <p class="text-muted mb-0">
                        Try changing your filter settings
                    </p>
                </td>
            </tr>
        `;
        return;
    }
    
    let html = '';
    analyses.forEach((analysis) => {
        html += createDetailedRow(analysis);
    });
    
    tableBody.innerHTML = html;
    attachViewButtonListeners();
}

function createCompactRow(analysis) {
    const fileInfo = analysis.file_info || {};
    const analysisData = analysis.analysis || {};
    const sat = analysisData.saturation_analysis || {};
    const sky = analysisData.sky_brightness || {};
    const snr = analysisData.snr_metrics || {};
    
    // Extract equipment
    const telescope = fileInfo.telescope || analysisData.telescope || 'Unknown';
    const camera = fileInfo.camera || analysisData.camera || 'Unknown';
    const rig = fileInfo.rig || `${camera.split(" ")[0]}/${telescope.split(" ")[0]}`;
    
    // Determine exposure badge
    const factor = analysisData.exposure_factor || 1;
    let exposureBadge = 'badge bg-success';
    if (factor > 1.5) exposureBadge = 'badge bg-warning';
    if (factor < 0.67) exposureBadge = 'badge bg-danger';
    
    // Determine sky brightness badge
    const skyMag = sky.mag_per_arcsec2;
    let skyBadge = 'badge bg-primary';
    if (skyMag && skyMag < 19) skyBadge = 'badge bg-secondary';
    
    // Parse RMS from filename
    let rmsValue = '--';
    const filename = fileInfo.filename || '';
    const rmsMatch = filename.match(/RMS_?(\d+\.?\d*)/i);
    if (rmsMatch) {
        rmsValue = parseFloat(rmsMatch[1]).toFixed(2);
    }
    
    // Determine status
    let status = 'Good';
    let statusBadge = 'badge bg-success';
    if (sat.severity === 'CRITICAL') {
        status = 'Critical';
        statusBadge = 'badge bg-danger';
    } else if (sat.severity === 'MODERATE') {
        status = 'Moderate';
        statusBadge = 'badge bg-warning';
    }
    
    // Format timestamp
    const timestamp = analysis.timestamp ? new Date(analysis.timestamp) : new Date();
    const timeStr = timestamp.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    const dateStr = timestamp.toLocaleDateString();
    
    return `
        <tr class="analysis-card ${sat.severity && sat.severity !== 'NONE' ? 'saturation-warning' : ''}">
            <td>
                <div class="text-truncate" style="max-width: 200px;" title="${filename}">
                    <strong>${filename}</strong>
                </div>
                <small class="text-muted">${dateStr} ${timeStr}</small>
            </td>
            <td><span class="badge bg-secondary">${fileInfo.object || 'Unknown'}</span></td>
            <td><span class="badge bg-info">${fileInfo.filter || 'N/A'}</span></td>
            <td><span class="badge rig-${rig}">${rig}</span></td>
            <td><small>${telescope}</small></td>
            <td><small>${camera}</small></td>
            <td>
                <span class="${exposureBadge}">
                    ${analysisData.current_exposure || 0}s
                </span>
            </td>
            <td>
                <span class="badge ${rmsValue !== '--' ? 'bg-primary' : 'bg-secondary'}">
                    ${rmsValue}" ${rmsValue !== '--' ? 'RMS' : ''}
                </span>
            </td>
            <td>
                ${skyMag ? `
                    <span class="${skyBadge}">
                        ${skyMag.toFixed(1)} mag/arcsec²
                    </span>
                ` : 'N/A'}
            </td>
            <td>
                <small>${snr.snr_background ? snr.snr_background.toFixed(1) : 'N/A'}</small>
            </td>
            <td class="text-muted">--</td>
            <td class="text-muted">--</td>
            <td>
                <span class="${statusBadge}">${status}</span>
            </td>
            <td>
                <button class="btn btn-sm btn-outline-info view-analysis-btn" data-filename="${filename}">
                    <i class="bi bi-eye"></i>
                </button>
            </td>
        </tr>
    `;
}

function createDetailedRow(analysis) {
    const fileInfo = analysis.file_info || {};
    const analysisData = analysis.analysis || {};
    const sat = analysisData.saturation_analysis || {};
    const sky = analysisData.sky_brightness || {};
    const snr = analysisData.snr_metrics || {};
    
    // Extract equipment
    const telescope = fileInfo.telescope || analysisData.telescope || 'Unknown';
    const camera = fileInfo.camera || analysisData.camera || 'Unknown';
    const rig = fileInfo.rig || `${camera.split(" ")[0]}/${telescope.split(" ")[0]}`;
    
    // Determine exposure badge
    const factor = analysisData.exposure_factor || 1;
    let exposureBadge = 'bg-success';
    if (factor > 1.5) exposureBadge = 'bg-warning';
    if (factor < 0.67) exposureBadge = 'bg-danger';
    
    // Determine sky brightness badge
    const skyMag = sky.mag_per_arcsec2;
    let skyBadge = 'bg-primary';
    if (skyMag && skyMag < 19) skyBadge = 'bg-secondary';
    
    // Parse RMS from filename
    let rmsValue = '--';
    const filename = fileInfo.filename || '';
    const rmsMatch = filename.match(/RMS_?(\d+\.?\d*)/i);
    if (rmsMatch) {
        rmsValue = parseFloat(rmsMatch[1]).toFixed(2);
    }
    
    // Determine status
    let status = 'Good';
    let statusBadge = 'status-Good';
    if (sat.severity === 'CRITICAL') {
        status = 'Critical';
        statusBadge = 'status-Critical';
    } else if (sat.severity === 'MODERATE') {
        status = 'Moderate';
        statusBadge = 'status-Moderate';
    }
    
    return `
        <tr class="analysis-card">
            <td>
                <div class="detailed-file-display">
                    <div class="filename-line" title="${filename}">
                        ${filename}
                    </div>
                    <div class="metrics-mini-table">
                        <div class="metric-header-row">
                            <div class="metric-header-cell"><i class="bi bi-star"></i>Object</div>
                            <div class="metric-header-cell"><i class="bi bi-funnel"></i>Filter</div>
                            <div class="metric-header-cell"><i class="bi bi-camera"></i>Rig</div>
                            <div class="metric-header-cell"><i class="bi bi-telescope"></i>Telescope</div>
                            <div class="metric-header-cell"><i class="bi bi-camera-video"></i>Camera</div>
                            <div class="metric-header-cell"><i class="bi bi-clock"></i>Exposure</div>
                            <div class="metric-header-cell"><i class="bi bi-bullseye"></i>RMS</div>
                        </div>
                        <div class="metric-value-row">
                            <div class="metric-value-cell">${fileInfo.object || 'N/A'}</div>
                            <div class="metric-value-cell"><span class="badge filter-${fileInfo.filter || 'Unknown'}">${fileInfo.filter || 'N/A'}</span></div>
                            <div class="metric-value-cell"><span class="badge rig-${rig}">${rig}</span></div>
                            <div class="metric-value-cell">${telescope}</div>
                            <div class="metric-value-cell">${camera}</div>
                            <div class="metric-value-cell"><span class="badge ${exposureBadge}">${analysisData.current_exposure || 0}s</span></div>
                            <div class="metric-value-cell"><span class="badge bg-info">${rmsValue}"</span></div>
                        </div>
                        <div class="metric-header-row">
                            <div class="metric-header-cell"><i class="bi bi-cloud-moon"></i>Sky</div>
                            <div class="metric-header-cell"><i class="bi bi-graph-up"></i>SNR</div>
                            <div class="metric-header-cell"><i class="bi bi-stars"></i>Stars</div>
                            <div class="metric-header-cell"><i class="bi bi-circle"></i>HFR</div>
                            <div class="metric-header-cell"><i class="bi bi-exclamation-triangle"></i>Status</div>
                            <div class="metric-header-cell"></div>
                            <div class="metric-header-cell"></div>
                        </div>
                        <div class="metric-value-row">
                            <div class="metric-value-cell">${skyMag ? `<span class="badge ${skyBadge}">${skyMag.toFixed(1)}</span>` : 'N/A'}</div>
                            <div class="metric-value-cell">${snr.snr_background ? `<span class="badge bg-success">${snr.snr_background.toFixed(1)}</span>` : 'N/A'}</div>
                            <div class="metric-value-cell"><span class="badge bg-secondary">--</span></div>
                            <div class="metric-value-cell"><span class="badge bg-secondary">--</span></div>
                            <div class="metric-value-cell"><span class="badge ${statusBadge}">${status}</span></div>
                            <div class="metric-value-cell"></div>
                            <div class="metric-value-cell"></div>
                        </div>
                    </div>
                </div>
            </td>
            <td>
                <button class="btn btn-sm btn-outline-info view-analysis-btn" data-filename="${filename}">
                    <i class="bi bi-eye"></i>
                </button>
            </td>
        </tr>
    `;
}

function attachViewButtonListeners() {
    document.querySelectorAll('.view-analysis-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const filename = this.getAttribute('data-filename');
            viewAnalysisDetails(filename);
        });
    });
}

function updateLastUpdateTime() {
    lastDataUpdate = new Date();
    const timeElement = document.getElementById('last-update-time');
    const statusElement = document.getElementById('last-update-status');
    
    if (timeElement && lastDataUpdate) {
        const timeStr = lastDataUpdate.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'});
        timeElement.textContent = timeStr;
    }
    
    if (statusElement) {
        statusElement.textContent = 'Data updated';
        statusElement.className = 'card-text text-success';
        
        // Clear success status after 5 seconds
        setTimeout(() => {
            if (statusElement) {
                statusElement.textContent = 'Auto-updating';
                statusElement.className = 'card-text text-muted';
            }
        }, 5000);
    }
}

function loadRigSummary() {
    // For now, generate from current analyses
    // Later: Get from dedicated API endpoint
    fetch(`/api/analyses?page=1&per_page=100`)
        .then(response => response.json())
        .then(data => {
            updateRigSummary(data.analyses || []);
        })
        .catch(error => {
            console.error('Error loading rig summary:', error);
        });
}

function updateRigSummary(analyses) {
    const tableBody = document.getElementById('rig-summary-table');
    if (!tableBody) return;
    
    if (!analyses || analyses.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">No data</td></tr>';
        return;
    }
    
    // Group analyses by rig
    const rigGroups = {};
    analyses.forEach(analysis => {
        const fileInfo = analysis.file_info || {};
        const telescope = fileInfo.telescope || 'Unknown';
        const camera = fileInfo.camera || 'Unknown';
        const rig = fileInfo.rig || `${camera.split(" ")[0]}/${telescope.split(" ")[0]}`;
        
        if (!rigGroups[rig]) {
            rigGroups[rig] = {
                rig: rig,
                telescope: telescope,
                camera: camera,
                count: 0
            };
        }
        rigGroups[rig].count++;
    });
    
    // Build table
    let html = '';
    Object.values(rigGroups).forEach(rig => {
        html += '<tr>';
        html += '<td><strong>' + rig.rig + '</strong></td>';
        html += '<td>' + rig.telescope + '</td>';
        html += '<td>' + rig.camera + '</td>';
        html += '<td class="text-end"><span class="badge bg-primary">' + rig.count + '</span></td>';
        html += '</tr>';
    });
    
    tableBody.innerHTML = html;
}

function updatePagination(data) {
    const pagination = document.getElementById('pagination');
    if (!pagination) return;
    
    const totalPages = data.pages || 1;
    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }
    
    let html = '';
    
    // Previous button
    html += `<li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
        <a class="page-link" href="#" onclick="loadAnalyses(${currentPage - 1}); return false;">Previous</a>
    </li>`;
    
    // Page numbers
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);
    
    for (let i = startPage; i <= endPage; i++) {
        html += `<li class="page-item ${i === currentPage ? 'active' : ''}">
            <a class="page-link" href="#" onclick="loadAnalyses(${i}); return false;">${i}</a>
        </li>`;
    }
    
    // Next button
    html += `<li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
        <a class="page-link" href="#" onclick="loadAnalyses(${currentPage + 1}); return false;">Next</a>
    </li>`;
    
    pagination.innerHTML = html;
}

function loadWatcherStatus() {
    fetch('/api/watcher/status')
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to get watcher status');
            }
            return response.json();
        })
        .then(data => {
            watcherRunning = data.watcher_running || false;
            updateWatcherControls(data);
        })
        .catch(error => {
            console.error('Error loading watcher status:', error);
        });
}

function updateWatcherControls(data) {
    const startBtn = document.getElementById('start-watcher-btn');
    const stopBtn = document.getElementById('stop-watcher-btn');
    const statusBadge = document.getElementById('watcher-status-badge');
    const statusText = document.getElementById('watcher-status-text');
    
    if (!startBtn || !stopBtn || !statusBadge) return;
    
    const isRunning = data.watcher_running || false;
    
    if (isRunning) {
        startBtn.disabled = true;
        stopBtn.disabled = false;
        statusBadge.className = 'badge bg-success';
        statusBadge.textContent = 'Running';
        if (statusText) statusText.textContent = 'Monitoring for new files';
        
        // Update watcher info
        const watcherInfo = document.getElementById('watcher-info');
        if (watcherInfo) {
            watcherInfo.innerHTML = `
                <div class="d-flex">
                    <i class="bi bi-check-circle me-2"></i>
                    <div>
                        <strong>Watcher Active:</strong> Monitoring for new FITS files.
                        <br><small>New files will be analyzed automatically.</small>
                    </div>
                </div>
            `;
            watcherInfo.className = 'alert alert-success';
        }
    } else {
        startBtn.disabled = false;
        stopBtn.disabled = true;
        statusBadge.className = 'badge bg-secondary';
        statusBadge.textContent = 'Stopped';
        if (statusText) statusText.textContent = 'Not monitoring';
        
        // Update watcher info
        const watcherInfo = document.getElementById('watcher-info');
        if (watcherInfo) {
            watcherInfo.innerHTML = `
                <div class="d-flex">
                    <i class="bi bi-info-circle me-2"></i>
                    <div>
                        <strong>New Files Only Mode:</strong> Only files added AFTER starting the watcher will be analyzed.
                        <br><small>Use "Process All" to analyze existing files.</small>
                    </div>
                </div>
            `;
            watcherInfo.className = 'alert alert-info';
        }
    }
}

function startWatcher() {
    showNotification('Starting watcher...', 'info');
    
    fetch('/api/watcher/start')
        .then(response => response.json())
        .then(data => {
            showNotification(data.message || 'Watcher started', 'success');
            loadWatcherStatus();
            
            // Refresh data after a short delay
            setTimeout(() => {
                refreshNow();
            }, 1000);
        })
        .catch(error => {
            console.error('Error starting watcher:', error);
            showNotification('Error starting watcher: ' + error.message, 'error');
        });
}

function stopWatcher() {
    if (confirm('Stop the watcher? New files will no longer be analyzed automatically.')) {
        showNotification('Stopping watcher...', 'info');
        
        fetch('/api/watcher/stop')
            .then(response => response.json())
            .then(data => {
                showNotification(data.message || 'Watcher stopped', 'success');
                loadWatcherStatus();
            })
            .catch(error => {
                console.error('Error stopping watcher:', error);
                showNotification('Error stopping watcher: ' + error.message, 'error');
            });
    }
}

function viewAnalysisDetails(filename) {
    if (!filename) {
        showNotification('No filename provided', 'error');
        return;
    }
    
    fetch(`/api/analysis/${encodeURIComponent(filename)}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Analysis not found');
            }
            return response.json();
        })
        .then(analysis => {
            showAnalysisModal(analysis);
        })
        .catch(error => {
            console.error('Error loading analysis details:', error);
            showNotification('Could not load analysis details', 'error');
        });
}

function showAnalysisModal(analysis) {
    const modalBody = document.getElementById('analysis-modal-body');
    if (!modalBody) {
        showNotification('Modal not found', 'error');
        return;
    }
    
    modalBody.innerHTML = createAnalysisDetailsHTML(analysis);
    
    const modalElement = document.getElementById('analysisModal');
    if (modalElement) {
        const modal = new bootstrap.Modal(modalElement);
        modal.show();
    }
}

function createAnalysisDetailsHTML(analysis) {
    const fileInfo = analysis.file_info || {};
    
    return `
        <div class="container-fluid">
            <div class="row">
                <div class="col-md-12">
                    <h5>${fileInfo.filename || 'Unknown File'}</h5>
                    <p class="text-muted">${analysis.timestamp ? new Date(analysis.timestamp).toLocaleString() : 'No timestamp'}</p>
                </div>
            </div>
            <div class="row mt-3">
                <div class="col-md-12">
                    <pre class="bg-light p-3 rounded" style="max-height: 400px; overflow: auto;">
${JSON.stringify(analysis, null, 2)}
                    </pre>
                </div>
            </div>
        </div>
    `;
}

function exportCurrentAnalysis() {
    showNotification('Export feature coming soon', 'info');
}

function processExistingFiles(count) {
    showNotification(`Processing ${count} existing files...`, 'info');
    // Implementation will be added later
}

function showNotification(message, type = 'info') {
    const toastEl = document.getElementById('notification-toast');
    const toastTitle = document.getElementById('toast-title');
    const toastMessage = document.getElementById('toast-message');
    
    if (!toastEl || !toastTitle || !toastMessage) return;
    
    // Set title and message
    toastTitle.textContent = type.charAt(0).toUpperCase() + type.slice(1);
    toastMessage.textContent = message;
    
    // Set color based on type
    const toast = new bootstrap.Toast(toastEl);
    toast.show();
}

function showError(message) {
    showNotification(message, 'error');
}

// Make functions available globally
window.loadAnalyses = loadAnalyses;
window.viewAnalysisDetails = viewAnalysisDetails;
window.startWatcher = startWatcher;
window.stopWatcher = stopWatcher;
window.refreshNow = refreshNow;
window.processExistingFiles = processExistingFiles;
