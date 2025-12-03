// Centaur Parting Dashboard JavaScript

let currentPage = 1;
const perPage = 20;
let autoRefreshInterval = null;
let watcherRunning = false;
let refreshInterval = 10000; // 10 seconds default
let countdownInterval = null;
let countdownValue = 10;
let lastDataUpdate = null;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard initialized');
    
    // Initialize components
    setupEventListeners();
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
}

function startAutoRefresh() {
    stopAutoRefresh(); // Clear any existing
    
    console.log(`Starting auto-refresh every ${refreshInterval/1000}s`);
    
    // Update UI
    document.getElementById('refresh-rate-text').textContent = `Rate: ${refreshInterval/1000}s`;
    
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
    document.getElementById('refresh-progress').style.width = '0%';
    document.getElementById('next-refresh-text').textContent = 'Auto-refresh stopped';
    document.getElementById('refresh-rate-text').textContent = 'Rate: Off';
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
        document.getElementById('refresh-progress').style.width = `${progressPercent}%`;
        
        // Update text
        document.getElementById('next-refresh-text').textContent = 
            `Next refresh in: ${countdownValue}s`;
            
    }, 1000);
}

function updateRefreshRateDisplay() {
    const rateText = refreshInterval === 0 ? 'Off' : `${refreshInterval/1000}s`;
    document.getElementById('refresh-rate-text').textContent = `Rate: ${rateText}`;
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
            updateAnalysesTable(data.analyses || []);
            updatePagination(data);
            updateLastUpdateTime();
            
            // Update displayed files count
            const countElement = document.getElementById('displayed-files-count');
            if (countElement) {
                countElement.textContent = `${data.analyses?.length || 0} files`;
            }
        })
        .catch(error => {
            console.error('Error loading analyses:', error);
            showError('Failed to load analyses: ' + error.message);
        });
}

function updateAnalysesTable(analyses) {
    const tableBody = document.getElementById('analyses-table');
    if (!tableBody) return;
    
    if (analyses.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="14" class="text-center text-muted py-4">
                    <i class="bi bi-inbox" style="font-size: 2rem;"></i><br>
                    No analyses yet. Start the watcher to analyze NEW files.
                </td>
            </tr>
        `;
        return;
    }
    
    let html = '';
    analyses.forEach((analysis) => {
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
        let exposureBadge = 'badge-exposure-good';
        if (factor > 1.5) exposureBadge = 'badge-exposure-high';
        if (factor < 0.67) exposureBadge = 'badge-exposure-low';
        
        // Determine sky brightness badge
        const skyMag = sky.mag_per_arcsec2;
        let skyBadge = 'sky-badge-dark';
        if (skyMag && skyMag < 19) skyBadge = 'sky-badge-bright';
        
        // Parse RMS from filename (placeholder - will be replaced with actual parsing)
        let rmsValue = '--';
        const filename = fileInfo.filename || '';
        const rmsMatch = filename.match(/RMS_?(\d+\.?\d*)/i);
        if (rmsMatch) {
            rmsValue = parseFloat(rmsMatch[1]).toFixed(2);
        }
        
        // Format timestamp
        const timestamp = analysis.timestamp ? new Date(analysis.timestamp) : new Date();
        const timeStr = timestamp.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        const dateStr = timestamp.toLocaleDateString();
        
        html += `
            <tr class="${sat.severity !== 'NONE' ? 'saturation-warning' : ''}">
                <td>
                    <div class="text-truncate" style="max-width: 200px;" title="${fileInfo.filename || 'Unknown'}">
                        <strong>${fileInfo.filename || 'Unknown'}</strong>
                    </div>
                    <small class="text-muted">${dateStr} ${timeStr}</small>
                </td>
                <td><span class="badge bg-secondary">${fileInfo.object || 'Unknown'}</span></td>
                <td><span class="badge bg-info">${fileInfo.filter || 'N/A'}</span></td>
                <td><small>${rig}</small></td>
                <td><small>${telescope}</small></td>
                <td><small>${camera}</small></td>
                <td>
                    <span class="badge ${exposureBadge}">
                        ${analysisData.current_exposure || 0}s
                    </span>
                    <br>
                    <small>${analysisData.recommended_exposure ? 'Rec: ' + analysisData.recommended_exposure.toFixed(0) + 's' : ''}</small>
                </td>
                <td>
                    <span class="badge ${rmsValue !== '--' ? 'bg-primary' : 'bg-secondary'}">
                        ${rmsValue}" ${rmsValue !== '--' ? 'RMS' : ''}
                    </span>
                </td>
                <td>
                    ${skyMag ? `
                        <span class="badge ${skyBadge}">
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
                    ${sat.severity && sat.severity !== 'NONE' ? 
                        `<span class="badge bg-warning">${sat.severity}</span>` : 
                        `<span class="badge bg-success">Good</span>`
                    }
                </td>
                <td>
                    <button class="btn btn-sm btn-outline-primary view-analysis-btn" 
                            onclick="viewAnalysisDetails('${fileInfo.filename || ''}')">
                        <i class="bi bi-eye"></i>
                    </button>
                </td>
            </tr>
        `;
    });
    
    tableBody.innerHTML = html;
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
    if (!tableBody || !analyses.length) {
        if (tableBody) {
            tableBody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">No data</td></tr>';
        }
        return;
    }
    
    // Group analyses by rig
    const rigGroups = {};
    analyses.forEach(analysis => {
        const fileInfo = analysis.file_info || {};
        const rig = fileInfo.rig || 'Unknown';
        
        if (!rigGroups[rig]) {
            rigGroups[rig] = {
                rig: rig,
                telescope: fileInfo.telescope || 'Unknown',
                camera: fileInfo.camera || 'Unknown',
                count: 0
            };
        }
        rigGroups[rig].count++;
    });
    
        // Build table
    let html = '';
    Object.values(rigGroups).forEach(rig => {
        const shortCamera = rig.camera.split(' ')[0];
        const shortScope = rig.telescope.split(' ')[0];
        
        html += '<tr>';
        html += '<td><small>' + rig.rig + '</small></td>';
        html += '<td><small>' + shortScope + '</small></td>';
        html += '<td><small>' + shortCamera + '</small></td>';
        html += '<td class="analysis-count">' + rig.count + '</td>';
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
                <i class="bi bi-check-circle"></i> 
                <strong>Watcher Active:</strong> Monitoring for new FITS files.
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
                <i class="bi bi-info-circle"></i> 
                <strong>New Files Only Mode:</strong> Only files added AFTER starting the watcher will be analyzed.
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
    // Simplified for now - will be enhanced later
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
    // Will be implemented when we have the analysis data in modal
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
