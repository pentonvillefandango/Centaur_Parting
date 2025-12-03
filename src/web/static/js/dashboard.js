// Centaur Parting Dashboard JavaScript

let currentPage = 1;
const perPage = 20;
let autoRefreshInterval = null;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    loadAnalyses();
    loadRecommendations();
    setupAutoRefresh();
    
    // Setup pagination event listeners
    document.getElementById('analyses-table').addEventListener('click', function(e) {
        if (e.target.classList.contains('view-analysis')) {
            const analysisId = e.target.dataset.analysisId;
            viewAnalysisDetails(analysisId);
        }
    });
});

function loadAnalyses(page = 1) {
    currentPage = page;
    fetch(`/api/analyses?page=${page}&per_page=${perPage}`)
        .then(response => response.json())
        .then(data => {
            updateAnalysesTable(data.analyses);
            updatePagination(data);
        })
        .catch(error => console.error('Error loading analyses:', error));
}

function updateAnalysesTable(analyses) {
    const tableBody = document.getElementById('analyses-table');
    tableBody.innerHTML = '';
    
    analyses.forEach(analysis => {
        const fileInfo = analysis.file_info;
        const analysisData = analysis.analysis;
        const sat = analysisData.saturation_analysis;
        
        const row = document.createElement('tr');
        row.className = sat.severity !== 'NONE' ? 'saturation-warning' : '';
        
        // Determine exposure badge
        const factor = analysisData.exposure_factor;
        let exposureBadge = 'badge-exposure-good';
        if (factor > 1.5) exposureBadge = 'badge-exposure-high';
        if (factor < 0.67) exposureBadge = 'badge-exposure-low';
        
        // Determine sky brightness badge
        const skyMag = analysisData.sky_brightness.mag_per_arcsec2;
        let skyBadge = 'sky-badge-dark';
        if (skyMag && skyMag < 19) skyBadge = 'sky-badge-bright';
        
        row.innerHTML = `
            <td>
                <div class="text-truncate" style="max-width: 200px;" title="${fileInfo.filename}">
                    ${fileInfo.filename}
                </div>
                <small class="text-muted">${new Date(analysis.timestamp).toLocaleString()}</small>
            </td>
            <td><strong>${fileInfo.object}</strong></td>
            <td><span class="badge bg-info">${fileInfo.filter}</span></td>
            <td>
                <span class="badge ${exposureBadge}">
                    ${analysisData.current_exposure}s
                </span>
                <br>
                <small>Rec: ${analysisData.recommended_exposure.toFixed(0)}s</small>
            </td>
            <td>
                ${skyMag ? `
                    <span class="badge ${skyBadge}">
                        ${skyMag.toFixed(1)} mag/arcsec²
                    </span>
                ` : 'N/A'}
            </td>
            <td>
                <small>Bkg: ${analysisData.snr_metrics.snr_background.toFixed(1)}</small><br>
                <small>Faint: ${analysisData.snr_metrics.snr_faint_object.toFixed(1)}</small>
            </td>
            <td>
                ${sat.severity !== 'NONE' ? 
                    `<span class="badge bg-warning">${sat.severity}</span>` : 
                    `<span class="badge bg-success">Good</span>`
                }
                ${sat.likely_hot_pixels ? '<br><small class="text-muted">Hot pixels</small>' : ''}
            </td>
            <td>
                <button class="btn btn-sm btn-outline-primary view-analysis" 
                        data-analysis-id="${analysis.file_info.filename}">
                    <i class="bi bi-eye"></i> View
                </button>
            </td>
        `;
        
        tableBody.appendChild(row);
    });
}

function updatePagination(data) {
    const pagination = document.getElementById('pagination');
    pagination.innerHTML = '';
    
    const totalPages = data.pages;
    
    // Previous button
    const prevLi = document.createElement('li');
    prevLi.className = `page-item ${currentPage === 1 ? 'disabled' : ''}`;
    prevLi.innerHTML = `<a class="page-link" href="#" onclick="loadAnalyses(${currentPage - 1})">Previous</a>`;
    pagination.appendChild(prevLi);
    
    // Page numbers
    for (let i = 1; i <= totalPages; i++) {
        const li = document.createElement('li');
        li.className = `page-item ${i === currentPage ? 'active' : ''}`;
        li.innerHTML = `<a class="page-link" href="#" onclick="loadAnalyses(${i})">${i}</a>`;
        pagination.appendChild(li);
    }
    
    // Next button
    const nextLi = document.createElement('li');
    nextLi.className = `page-item ${currentPage === totalPages ? 'disabled' : ''}`;
    nextLi.innerHTML = `<a class="page-link" href="#" onclick="loadAnalyses(${currentPage + 1})">Next</a>`;
    pagination.appendChild(nextLi);
}

function loadRecommendations() {
    fetch('/api/recommendations')
        .then(response => response.json())
        .then(recommendations => {
            const container = document.getElementById('recommendations-list');
            container.innerHTML = '';
            
            if (recommendations.length === 0) {
                container.innerHTML = '<p class="text-muted">No recommendations yet. Process some files first.</p>';
                return;
            }
            
            // Group by type
            const grouped = {};
            recommendations.forEach(rec => {
                const key = rec.recommendation.substring(0, 50);
                if (!grouped[key]) {
                    grouped[key] = {
                        recommendation: rec.recommendation,
                        count: 0,
                        files: []
                    };
                }
                grouped[key].count++;
                grouped[key].files.push(rec.file);
            });
            
            // Display top 5 recommendations
            Object.values(grouped)
                .sort((a, b) => b.count - a.count)
                .slice(0, 5)
                .forEach(item => {
                    const div = document.createElement('div');
                    div.className = 'mb-2';
                    div.innerHTML = `
                        <div class="d-flex justify-content-between align-items-start">
                            <div>
                                <strong>${item.recommendation}</strong>
                                <br>
                                <small class="text-muted">Applies to ${item.count} file(s)</small>
                            </div>
                            <span class="badge bg-primary">${item.count}</span>
                        </div>
                    `;
                    container.appendChild(div);
                });
        })
        .catch(error => console.error('Error loading recommendations:', error));
}

function viewAnalysisDetails(filename) {
    fetch(`/api/analyze/${encodeURIComponent(filename)}`)
        .then(response => response.json())
        .then(analysis => {
            const modalBody = document.getElementById('analysis-details');
            modalBody.innerHTML = createAnalysisDetailsHTML(analysis);
            
            const modal = new bootstrap.Modal(document.getElementById('analysisModal'));
            modal.show();
        })
        .catch(error => {
            console.error('Error loading analysis details:', error);
            alert('Error loading analysis details: ' + error.message);
        });
}

function createAnalysisDetailsHTML(analysis) {
    const fileInfo = analysis.file_info;
    const analysisData = analysis.analysis;
    const sat = analysisData.saturation_analysis;
    const sky = analysisData.sky_brightness;
    const snr = analysisData.snr_metrics;
    
    return `
        <div class="container-fluid">
            <div class="row">
                <div class="col-md-6">
                    <h6>File Information</h6>
                    <table class="table table-sm">
                        <tr><td>Filename:</td><td><strong>${fileInfo.filename}</strong></td></tr>
                        <tr><td>Object:</td><td>${fileInfo.object}</td></tr>
                        <tr><td>Filter:</td><td>${fileInfo.filter}</td></tr>
                        <tr><td>Dimensions:</td><td>${fileInfo.dimensions.join(' × ')}</td></tr>
                        <tr><td>Exposure:</td><td>${analysisData.current_exposure}s</td></tr>
                    </table>
                </div>
                <div class="col-md-6">
                    <h6>Exposure Analysis</h6>
                    <table class="table table-sm">
                        <tr><td>Current:</td><td><strong>${analysisData.current_exposure}s</strong></td></tr>
                        <tr><td>Recommended:</td><td><strong>${analysisData.recommended_exposure.toFixed(0)}s</strong></td></tr>
                        <tr><td>Factor:</td><td>${analysisData.exposure_factor.toFixed(2)}x</td></tr>
                        <tr><td>Optimal Sub:</td><td>${analysisData.optimal_sub_length.toFixed(0)}s</td></tr>
                        <tr><td>Noise Regime:</td><td>${analysisData.noise_regime.read_noise_dominant ? 'Read-noise' : 'Sky-noise'} limited</td></tr>
                    </table>
                </div>
            </div>
            
            <div class="row mt-3">
                <div class="col-md-4">
                    <h6>Signal-to-Noise</h6>
                    <table class="table table-sm">
                        <tr><td>Background SNR:</td><td>${snr.snr_background.toFixed(1)}</td></tr>
                        <tr><td>Faint Object SNR:</td><td>${snr.snr_faint_object.toFixed(1)}</td></tr>
                        <tr><td>Moderate Object SNR:</td><td>${snr.snr_moderate_object.toFixed(1)}</td></tr>
                    </table>
                </div>
                <div class="col-md-4">
                    <h6>Sky Brightness</h6>
                    <table class="table table-sm">
                        <tr><td>Magnitude:</td><td>${sky.mag_per_arcsec2 ? sky.mag_per_arcsec2.toFixed(1) + ' mag/arcsec²' : 'N/A'}</td></tr>
                        <tr><td>Electrons/pixel:</td><td>${sky.electrons_per_pixel.toFixed(0)} e⁻</td></tr>
                        <tr><td>Rate:</td><td>${sky.electrons_per_second_per_pixel.toFixed(2)} e⁻/s/pixel</td></tr>
                    </table>
                </div>
                <div class="col-md-4">
                    <h6>Saturation</h6>
                    <table class="table table-sm">
                        <tr><td>Max Value:</td><td>${sat.max_value.toFixed(0)} ADU</td></tr>
                        <tr><td>Saturation Level:</td><td>${sat.saturation_level.toFixed(0)} ADU</td></tr>
                        <tr><td>Near-saturated:</td><td>${sat.near_saturated_pixels} (${sat.near_saturated_percent.toFixed(4)}%)</td></tr>
                        <tr><td>Severity:</td><td>${sat.severity}</td></tr>
                        <tr><td>Hot Pixels:</td><td>${sat.likely_hot_pixels ? 'Yes' : 'No'}</td></tr>
                    </table>
                </div>
            </div>
            
            <div class="row mt-3">
                <div class="col-12">
                    <h6>SHO Recommendation</h6>
                    <div class="alert alert-info">
                        <strong>SII/OIII Adjustment:</strong> ${analysisData.sho_recommendation.adjustment_factor.toFixed(2)}x<br>
                        <strong>Recommended Exposure:</strong> ${analysisData.sho_recommendation.recommended_exposure.toFixed(0)}s
                    </div>
                </div>
            </div>
            
            <div class="row mt-3">
                <div class="col-12">
                    <h6>Recommendations</h6>
                    <ul class="list-group">
                        ${analysis.recommendations.map(rec => `
                            <li class="list-group-item">${rec}</li>
                        `).join('')}
                    </ul>
                </div>
            </div>
        </div>
    `;
}

function startWatcher() {
    fetch('/api/start_watcher')
        .then(response => response.json())
        .then(data => {
            alert(data.message);
        })
        .catch(error => {
            alert('Error starting watcher: ' + error.message);
        });
}

function processExisting(count) {
    fetch(`/api/process_existing?count=${count}`)
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            setTimeout(() => {
                loadAnalyses();
                loadRecommendations();
            }, 2000);
        })
        .catch(error => {
            alert('Error processing files: ' + error.message);
        });
}

function refreshAnalyses() {
    loadAnalyses(currentPage);
    loadRecommendations();
    updateStats();
}

function updateStats() {
    fetch('/api/stats')
        .then(response => response.json())
        .then(stats => {
            document.getElementById('total-analyses').textContent = stats.total_analyses;
            document.getElementById('avg-exposure').textContent = stats.exposure_stats.avg_exposure.toFixed(0) + 's';
            if (stats.sky_brightness_stats.avg_mag) {
                document.getElementById('avg-sky').textContent = stats.sky_brightness_stats.avg_mag.toFixed(1);
            }
            document.getElementById('filter-count').textContent = Object.keys(stats.by_filter).length;
        });
}

function setupAutoRefresh() {
    const autoRefreshCheckbox = document.getElementById('auto-refresh');
    
    autoRefreshCheckbox.addEventListener('change', function() {
        if (this.checked) {
            autoRefreshInterval = setInterval(refreshAnalyses, 30000); // 30 seconds
        } else {
            clearInterval(autoRefreshInterval);
            autoRefreshInterval = null;
        }
    });
    
    // Start auto-refresh if checked
    if (autoRefreshCheckbox.checked) {
        autoRefreshInterval = setInterval(refreshAnalyses, 30000);
    }
}
