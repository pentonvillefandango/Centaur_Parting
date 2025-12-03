// Centaur Parting Dashboard JavaScript

let currentPage = 1;
const perPage = 20;
let autoRefreshInterval = null;
let watcherRunning = false;
let refreshCountdown = 10;
let lastUpdateTime = null;
let statusPollingInterval = null;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard initialized');
    loadAnalyses();
    loadWatcherStatus();
    setupAutoRefresh();
    setupEventListeners();
    startStatusPolling();
    startCountdownTimer();
});

function setupEventListeners() {
    // Start/Stop watcher buttons
    const startBtn = document.getElementById('start-watcher-btn');
    const stopBtn = document.getElementById('stop-watcher-btn');
    const refreshBtn = document.getElementById('refresh-btn');
    
    if (startBtn) startBtn.addEventListener('click', startWatcher);
    if (stopBtn) stopBtn.addEventListener('click', stopWatcher);
    if (refreshBtn) refreshBtn.addEventListener('click', refreshDashboard);
    
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
    
    // Auto-refresh checkbox
    const autoRefreshCheckbox = document.getElementById('auto-refresh-checkbox');
    if (autoRefreshCheckbox) {
        autoRefreshCheckbox.addEventListener('change', function() {
            if (this.checked && watcherRunning) {
                startAutoRefresh();
            } else {
                stopAutoRefresh();
            }
            updateAutoRefreshIndicator();
        });
    }
}

function startStatusPolling() {
    // Clear any existing polling
    if (statusPollingInterval) {
        clearInterval(statusPollingInterval);
    }
    
    // Poll for watcher status every 3 seconds
    statusPollingInterval = setInterval(loadWatcherStatus, 3000);
    console.log('Started status polling (3s interval)');
}

function startCountdownTimer() {
    // Update countdown every second
    setInterval(() => {
        if (refreshCountdown > 0) {
            refreshCountdown--;
            updateRefreshCountdown();
        }
    }, 1000);
}

function loadAnalyses(page = 1) {
    currentPage = page;
    console.log('Loading analyses, page:', page);
    
    fetch(`/api/analyses?page=${page}&per_page=${perPage}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log('Analyses loaded:', data.analyses?.length || 0, 'items');
            updateAnalysesTable(data.analyses || []);
            updatePagination(data);
            updateStats(data);
            lastUpdateTime = new Date();
            updateLastUpdateTime();
            
            // Reset countdown on successful load
            if (autoRefreshInterval && watcherRunning) {
                refreshCountdown = 10;
                updateRefreshCountdown();
            }
        })
        .catch(error => {
            console.error('Error loading analyses:', error);
            showError('Failed to load analyses: ' + error.message);
        });
}

function updateAnalysesTable(analyses) {
    const tableBody = document.getElementById('analyses-table');
    if (!tableBody) {
        console.error('Analyses table not found');
        return;
    }
    
    console.log('Updating table with', analyses.length, 'analyses');
    
    if (analyses.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center text-muted py-4">
                    <i class="bi bi-inbox" style="font-size: 2rem;"></i><br>
                    No analyses yet. Start the watcher to analyze NEW files.
                </td>
            </tr>
        `;
        return;
    }
    
    let html = '';
    analyses.forEach((analysis, index) => {
        const fileInfo = analysis.file_info || {};
        const analysisData = analysis.analysis || {};
        const sat = analysisData.saturation_analysis || {};
        const sky = analysisData.sky_brightness || {};
        const snr = analysisData.snr_metrics || {};
        
        // Determine exposure badge
        const factor = analysisData.exposure_factor || 1;
        let exposureBadge = 'badge-exposure-good';
        if (factor > 1.5) exposureBadge = 'badge-exposure-high';
        if (factor < 0.67) exposureBadge = 'badge-exposure-low';
        
        // Determine sky brightness badge
        const skyMag = sky.mag_per_arcsec2;
        let skyBadge = 'sky-badge-dark';
        if (skyMag && skyMag < 19) skyBadge = 'sky-badge-bright';
        
        // Format timestamp
        const timestamp = analysis.timestamp ? new Date(analysis.timestamp) : new Date();
        const timeStr = timestamp.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        const dateStr = timestamp.toLocaleDateString();
        
        html += `
            <tr class="${sat.severity !== 'NONE' ? 'saturation-warning' : ''}">
                <td>
                    <div class="text-truncate" style="max-width: 250px;" title="${fileInfo.filename || 'Unknown'}">
                        <strong>${fileInfo.filename || 'Unknown'}</strong>
                    </div>
                    <small class="text-muted">${dateStr} ${timeStr}</small>
                </td>
                <td><span class="badge bg-secondary">${fileInfo.object || 'Unknown'}</span></td>
                <td><span class="badge bg-info">${fileInfo.filter || 'N/A'}</span></td>
                <td>
                    <span class="badge ${exposureBadge}">
                        ${analysisData.current_exposure || 0}s
                    </span>
                    <br>
                    <small>${analysisData.recommended_exposure ? 'Rec: ' + analysisData.recommended_exposure.toFixed(0) + 's' : ''}</small>
                </td>
                <td>
                    ${skyMag ? `
                        <span class="badge ${skyBadge}">
                            ${skyMag.toFixed(1)} mag/arcsec²
                        </span>
                    ` : 'N/A'}
                </td>
                <td>
                    <small>Bkg: ${snr.snr_background ? snr.snr_background.toFixed(1) : 'N/A'}</small><br>
                    <small>Faint: ${snr.snr_faint_object ? snr.snr_faint_object.toFixed(1) : 'N/A'}</small>
                </td>
                <td>
                    ${sat.severity && sat.severity !== 'NONE' ? 
                        `<span class="badge bg-warning">${sat.severity}</span>` : 
                        `<span class="badge bg-success">Good</span>`
                    }
                    ${sat.likely_hot_pixels ? '<br><small class="text-muted">Hot pixels</small>' : ''}
                </td>
                <td>
                    <button class="btn btn-sm btn-outline-primary view-analysis-btn" 
                            data-filename="${fileInfo.filename || ''}"
                            title="View detailed analysis"
                            onclick="viewAnalysisDetails('${fileInfo.filename || ''}')">
                        <i class="bi bi-eye"></i> View
                    </button>
                </td>
            </tr>
        `;
    });
    
    tableBody.innerHTML = html;
    
    // Update analyses count badge
    const analysesCount = document.getElementById('analyses-count');
    if (analysesCount) {
        analysesCount.textContent = `${analyses.length} file${analyses.length !== 1 ? 's' : ''}`;
    }
}

function updateLastUpdateTime() {
    const timeElement = document.getElementById('last-update-time');
    if (timeElement && lastUpdateTime) {
        const timeStr = lastUpdateTime.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'});
        timeElement.textContent = timeStr;
    }
    
    // Update status indicator
    const statusText = document.getElementById('status-text');
    if (statusText && lastUpdateTime) {
        const now = new Date();
        const secondsAgo = Math.floor((now - lastUpdateTime) / 1000);
        statusText.textContent = `Updated ${secondsAgo}s ago`;
    }
}

function updateRefreshCountdown() {
    const progressBar = document.getElementById('refresh-progress');
    const countdownText = document.getElementById('next-refresh-text');
    
    if (progressBar && countdownText) {
        if (watcherRunning && autoRefreshInterval) {
            const progress = 100 - (refreshCountdown * 10); // 10 seconds total
            progressBar.style.width = `${progress}%`;
            progressBar.className = 'progress-bar bg-info';
            countdownText.textContent = `Next refresh in: ${refreshCountdown}s`;
        } else {
            progressBar.style.width = '0%';
            progressBar.className = 'progress-bar bg-secondary';
            countdownText.textContent = 'Auto-refresh paused';
        }
    }
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

function updateStats(data) {
    // Update total analyses count
    const totalElement = document.getElementById('total-analyses-count');
    if (totalElement) {
        totalElement.textContent = data.total || 0;
    }
    
    // Update last update display
    updateLastUpdateTime();
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
            console.log('Watcher status:', data);
            watcherRunning = data.watcher_running || false;
            updateWatcherControls(data);
            updateAutoRefreshIndicator();
            
            // If watcher just started running, refresh data immediately
            if (watcherRunning) {
                const autoRefreshCheckbox = document.getElementById('auto-refresh-checkbox');
                if (autoRefreshCheckbox && autoRefreshCheckbox.checked) {
                    // Start auto-refresh if not already running
                    if (!autoRefreshInterval) {
                        startAutoRefresh();
                    }
                    // Refresh data immediately when watcher starts
                    loadAnalyses(currentPage);
                }
            } else {
                // Watcher stopped, stop auto-refresh
                stopAutoRefresh();
            }
        })
        .catch(error => {
            console.error('Error loading watcher status:', error);
        });
}

function updateWatcherControls(data) {
    const startBtn = document.getElementById('start-watcher-btn');
    const stopBtn = document.getElementById('stop-watcher-btn');
    const statusBadge = document.getElementById('watcher-status-badge');
    const statusIndicator = document.getElementById('watcher-status-indicator');
    
    if (!startBtn || !stopBtn || !statusBadge) return;
    
    const isRunning = data.watcher_running || false;
    
    if (isRunning) {
        startBtn.disabled = true;
        stopBtn.disabled = false;
        statusBadge.className = 'badge bg-success';
        statusBadge.textContent = `Running`;
        if (statusIndicator) {
            statusIndicator.className = 'badge bg-success';
            statusIndicator.textContent = 'Running';
        }
        
        // Update watcher info message
        const watcherInfo = document.getElementById('watcher-info');
        if (watcherInfo) {
            watcherInfo.innerHTML = `
                <i class="bi bi-check-circle"></i> 
                <strong>Watcher Active:</strong> Monitoring for new FITS files. 
                ${data.total_new_files || 0} new files analyzed.
            `;
            watcherInfo.className = 'alert alert-success';
        }
    } else {
        startBtn.disabled = false;
        stopBtn.disabled = true;
        statusBadge.className = 'badge bg-secondary';
        statusBadge.textContent = 'Stopped';
        if (statusIndicator) {
            statusIndicator.className = 'badge bg-secondary';
            statusIndicator.textContent = 'Stopped';
        }
        
        // Update watcher info message
        const watcherInfo = document.getElementById('watcher-info');
        if (watcherInfo) {
            watcherInfo.innerHTML = `
                <i class="bi bi-info-circle"></i> 
                <strong>New Files Only Mode:</strong> Only files added AFTER starting the watcher will be analyzed and displayed.
                Existing files in /Volumes/Rig24_Imaging will be ignored.
            `;
            watcherInfo.className = 'alert alert-info';
        }
    }
}

function updateAutoRefreshIndicator() {
    const autoRefreshStatus = document.getElementById('auto-refresh-status');
    const autoRefreshIndicator = document.getElementById('auto-refresh-indicator');
    const autoRefreshCheckbox = document.getElementById('auto-refresh-checkbox');
    
    if (autoRefreshStatus) {
        if (watcherRunning && autoRefreshCheckbox && autoRefreshCheckbox.checked) {
            autoRefreshStatus.textContent = 'On';
            autoRefreshStatus.className = 'badge bg-success';
        } else {
            autoRefreshStatus.textContent = 'Off';
            autoRefreshStatus.className = 'badge bg-secondary';
        }
    }
    
    if (autoRefreshIndicator) {
        if (watcherRunning && autoRefreshCheckbox && autoRefreshCheckbox.checked) {
            autoRefreshIndicator.className = 'badge bg-success';
            autoRefreshIndicator.textContent = 'Auto-refresh: On';
        } else {
            autoRefreshIndicator.className = 'badge bg-info';
            autoRefreshIndicator.textContent = 'Auto-refresh: Off';
        }
    }
}

function viewAnalysisDetails(filename) {
    if (!filename) {
        alert('No filename provided');
        return;
    }
    
    console.log('Viewing analysis for:', filename);
    
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
            showError('Could not load analysis details: ' + error.message);
        });
}

function showAnalysisModal(analysis) {
    const modalBody = document.getElementById('analysis-modal-body');
    if (!modalBody) {
        alert('Modal not found');
        return;
    }
    
    modalBody.innerHTML = createAnalysisDetailsHTML(analysis);
    
    // Initialize Bootstrap modal
    const modalElement = document.getElementById('analysisModal');
    if (modalElement) {
        const modal = new bootstrap.Modal(modalElement);
        modal.show();
    }
}

function createAnalysisDetailsHTML(analysis) {
    const fileInfo = analysis.file_info || {};
    const analysisData = analysis.analysis || {};
    const sat = analysisData.saturation_analysis || {};
    const sky = analysisData.sky_brightness || {};
    const snr = analysisData.snr_metrics || {};
    const noise = analysisData.noise_regime || {};
    const sho = analysisData.sho_recommendation || {};
    const recommendations = analysis.recommendations || [];
    
    return `
        <div class="container-fluid">
            <div class="row">
                <div class="col-md-12">
                    <h5>${fileInfo.filename || 'Unknown File'}</h5>
                    <p class="text-muted">${analysis.timestamp ? new Date(analysis.timestamp).toLocaleString() : 'No timestamp'}</p>
                </div>
            </div>
            
            <div class="row mt-3">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h6 class="mb-0">File Information</h6>
                        </div>
                        <div class="card-body">
                            <table class="table table-sm table-borderless">
                                <tr><td><strong>Object:</strong></td><td>${fileInfo.object || 'Unknown'}</td></tr>
                                <tr><td><strong>Filter:</strong></td><td>${fileInfo.filter || 'N/A'}</td></tr>
                                <tr><td><strong>Dimensions:</strong></td><td>${fileInfo.dimensions ? fileInfo.dimensions.join(' × ') : 'N/A'}</td></tr>
                                <tr><td><strong>Exposure:</strong></td><td><strong>${analysisData.current_exposure || 0}s</strong></td></tr>
                            </table>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h6 class="mb-0">Exposure Analysis</h6>
                        </div>
                        <div class="card-body">
                            <table class="table table-sm table-borderless">
                                <tr><td><strong>Recommended:</strong></td><td><span class="badge bg-primary">${analysisData.recommended_exposure ? analysisData.recommended_exposure.toFixed(0) + 's' : 'N/A'}</span></td></tr>
                                <tr><td><strong>Factor:</strong></td><td>${analysisData.exposure_factor ? analysisData.exposure_factor.toFixed(2) + 'x' : 'N/A'}</td></tr>
                                <tr><td><strong>Optimal Sub:</strong></td><td>${analysisData.optimal_sub_length ? analysisData.optimal_sub_length.toFixed(0) + 's' : 'N/A'}</td></tr>
                                <tr><td><strong>Noise Regime:</strong></td><td>${noise.read_noise_dominant ? 'Read-noise limited' : 'Sky-noise limited'}</td></tr>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mt-3">
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-header">
                            <h6 class="mb-0">Signal-to-Noise</h6>
                        </div>
                        <div class="card-body">
                            <table class="table table-sm table-borderless">
                                <tr><td><strong>Background:</strong></td><td>${snr.snr_background ? snr.snr_background.toFixed(1) : 'N/A'}</td></tr>
                                <tr><td><strong>Faint Object:</strong></td><td>${snr.snr_faint_object ? snr.snr_faint_object.toFixed(1) : 'N/A'}</td></tr>
                                <tr><td><strong>Moderate Object:</strong></td><td>${snr.snr_moderate_object ? snr.snr_moderate_object.toFixed(1) : 'N/A'}</td></tr>
                            </table>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-header">
                            <h6 class="mb-0">Sky Brightness</h6>
                        </div>
                        <div class="card-body">
                            <table class="table table-sm table-borderless">
                                <tr><td><strong>Magnitude:</strong></td><td>${sky.mag_per_arcsec2 ? sky.mag_per_arcsec2.toFixed(1) + ' mag/arcsec²' : 'N/A'}</td></tr>
                                <tr><td><strong>Electrons/pixel:</strong></td><td>${sky.electrons_per_pixel ? sky.electrons_per_pixel.toFixed(0) + ' e⁻' : 'N/A'}</td></tr>
                                <tr><td><strong>Rate:</strong></td><td>${sky.electrons_per_second_per_pixel ? sky.electrons_per_second_per_pixel.toFixed(2) + ' e⁻/s/pixel' : 'N/A'}</td></tr>
                            </table>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-header">
                            <h6 class="mb-0">Saturation Analysis</h6>
                        </div>
                        <div class="card-body">
                            <table class="table table-sm table-borderless">
                                <tr><td><strong>Max Value:</strong></td><td>${sat.max_value ? sat.max_value.toFixed(0) + ' ADU' : 'N/A'}</td></tr>
                                <tr><td><strong>Saturation:</strong></td><td>${sat.saturation_level ? sat.saturation_level.toFixed(0) + ' ADU' : 'N/A'}</td></tr>
                                <tr><td><strong>Near-saturated:</strong></td><td>${sat.near_saturated_pixels ? sat.near_saturated_pixels + ' pixels (' + sat.near_saturated_percent.toFixed(4) + '%)' : 'N/A'}</td></tr>
                                <tr><td><strong>Severity:</strong></td><td><span class="badge ${sat.severity && sat.severity !== 'NONE' ? 'bg-warning' : 'bg-success'}">${sat.severity || 'Good'}</span></td></tr>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
            
            ${recommendations.length > 0 ? `
            <div class="row mt-3">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header">
                            <h6 class="mb-0">Recommendations</h6>
                        </div>
                        <div class="card-body p-0">
                            <ul class="list-group list-group-flush">
                                ${recommendations.map(rec => `<li class="list-group-item">${rec}</li>`).join('')}
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
            ` : ''}
        </div>
    `;
}

function startWatcher() {
    console.log('Starting watcher...');
    
    fetch('/api/watcher/start')
        .then(response => response.json())
        .then(data => {
            console.log('Watcher start response:', data);
            showMessage(data.message || 'Watcher started');
            loadWatcherStatus();
            
            // Refresh analyses after a short delay
            setTimeout(() => {
                loadAnalyses(1);
            }, 1000);
        })
        .catch(error => {
            console.error('Error starting watcher:', error);
            showError('Error starting watcher: ' + error.message);
        });
}

function stopWatcher() {
    if (confirm('Stop the watcher? New files will no longer be analyzed automatically.')) {
        console.log('Stopping watcher...');
        
        fetch('/api/watcher/stop')
            .then(response => response.json())
            .then(data => {
                console.log('Watcher stop response:', data);
                showMessage(data.message || 'Watcher stopped');
                loadWatcherStatus();
                stopAutoRefresh();
            })
            .catch(error => {
                console.error('Error stopping watcher:', error);
                showError('Error stopping watcher: ' + error.message);
            });
    }
}

function startAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
    
    console.log('Starting auto-refresh (10s interval)');
    autoRefreshInterval = setInterval(() => {
        if (watcherRunning) {
            console.log('Auto-refreshing analyses...');
            loadAnalyses(currentPage);
        }
        updateRefreshCountdown();
    }, 10000); // 10 seconds
    
    // Start countdown
    refreshCountdown = 10;
    updateRefreshCountdown();
    updateAutoRefreshIndicator();
}

function stopAutoRefresh() {
    if (autoRefreshInterval) {
        console.log('Stopping auto-refresh');
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
    updateRefreshCountdown();
    updateAutoRefreshIndicator();
}

function refreshDashboard() {
    console.log('Manual refresh');
    loadAnalyses(currentPage);
    loadWatcherStatus();
    
    // Reset countdown on manual refresh
    if (watcherRunning && autoRefreshInterval) {
        refreshCountdown = 10;
        updateRefreshCountdown();
    }
}

function setupAutoRefresh() {
    const autoRefreshCheckbox = document.getElementById('auto-refresh-checkbox');
    if (!autoRefreshCheckbox) return;
    
    // Start auto-refresh if checked and watcher is running
    if (autoRefreshCheckbox.checked && watcherRunning) {
        startAutoRefresh();
    }
}

function processExistingFiles(count) {
    alert(`To process ${count} existing files, use the command line or implement this feature.\n\nFor now, use: python -m monitor.enhanced_polling_watcher --process-existing --max-files ${count}`);
}

function showMessage(message) {
    // Create a temporary alert
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-success alert-dismissible fade show';
    alertDiv.style.position = 'fixed';
    alertDiv.style.top = '20px';
    alertDiv.style.right = '20px';
    alertDiv.style.zIndex = '9999';
    alertDiv.style.minWidth = '300px';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Remove after 3 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.parentNode.removeChild(alertDiv);
        }
    }, 3000);
}

function showError(message) {
    console.error('Error:', message);
    alert('Error: ' + message);
}

// Make functions available globally
window.loadAnalyses = loadAnalyses;
window.viewAnalysisDetails = viewAnalysisDetails;
window.startWatcher = startWatcher;
window.stopWatcher = stopWatcher;
window.refreshDashboard = refreshDashboard;
