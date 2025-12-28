async function initJobTracking() {
    console.log('Initializing Job Tracking...');
    states = await window.pywebview.api.get_job_application_states();
    
    populateStateSelect(document.getElementById('job_state'));
    
    await loadJobTrackingConfig();
}

function populateStateSelect(selectElement) {
    if (selectElement && states && Array.isArray(states)) {
        selectElement.innerHTML = '';
        states.forEach(state => {
            const option = document.createElement('option');
            option.value = state;
            option.textContent = getStateLabel(state);
            selectElement.appendChild(option);
        });
    }
}

function createStateSelect() {
    const stateSelect = document.createElement('select');
    stateSelect.className = 'form-select form-select-sm';
    populateStateSelect(stateSelect);
    return stateSelect;
}

async function loadJobTrackingConfig() {
    const companyName = config.job_tracking.company_name || '';
    const job = {
        'job_title': config.job_tracking.job_title || '',
        'job_url': config.job_tracking.job_url || '',
        'contact_name': config.job_tracking.contact_name || '',
        'contact_linkedin': config.job_tracking.contact_linkedin || '',
        'contact_email': config.job_tracking.contact_email || '',
        'job_state': config.job_tracking.job_state || ''
    };

    addJobToTable(job, companyName);

    console.log('Job tracking config loaded successfully');
}


function addJobToTable(job, companyName) {
    const tableBody = document.getElementById('job-table-body');
    const row = document.createElement('tr');
    
    row.innerHTML = `
        <td><input type="text" class="form-control form-control-sm company-name" value="${companyName || ''}"></td>
        <td><input type="text" class="form-control form-control-sm job-title" value="${job.job_title || ''}"></td>
        <td><input type="text" class="form-control form-control-sm job-url" value="${job.job_url || ''}"></td>
        <td class="state-cell"></td>
        <td><input type="text" class="form-control form-control-sm contact-name" value="${job.contact_name || ''}"></td>        
        <td><input type="text" class="form-control form-control-sm contact-linkedin" value="${job.contact_linkedin || ''}"></td>
        <td><input type="text" class="form-control form-control-sm contact-email" value="${job.contact_email || ''}"></td>
        <td>
            <div class="d-flex gap-2">
                <button class="btn btn-primary btn-sm w-100 track-job-row-btn">Track</button>
                <button class="btn btn-secondary btn-sm w-100 view-jobs-row-btn">View</button>
            </div>
        </td>
    `;

    // Create and insert the select element
    const stateSelect = createStateSelect();
    const stateCell = row.querySelector('.state-cell');
    stateCell.appendChild(stateSelect);

    // Set the select value (or default to first option)
    if (job.job_state && stateSelect.querySelector(`option[value="${job.job_state}"]`)) {
        stateSelect.value = job.job_state;
    }

    // Add event listeners
    row.querySelector('.track-job-row-btn').addEventListener('click', async () => {
        await trackJobApplicationFromRow(getRowData(row));
    });

    row.querySelector('.view-jobs-row-btn').addEventListener('click', async () => {
        await viewJobApplicationsFromRow(getRowData(row).company_name);
    });

    tableBody.prepend(row);
}


function getStateLabel(enumName) {
    const stateLabels = {
        'CONNECTION_REQUESTED': 'Request Sent',
        'MESSAGE_SENT': 'Message Sent',
        'EMAIL_SENT': 'Email Sent',
        'APPLIED': 'Applied',
        'UNKNOWN': 'Unknown'
    };
    return stateLabels[enumName] || enumName;
}




async function saveJobTrackingConfig(jobData) {
    const jobTrackingConfig = {
        company_name: jobData.company_name || '',
        job_title: jobData.job_title || '',
        job_url: jobData.job_url || '',
        contact_name: jobData.contact_name || '',
        contact_linkedin: jobData.contact_linkedin || '',
        contact_email: jobData.contact_email || '',
        job_state: jobData.job_state || ''
    };
    try {

        await window.pywebview.api.save_configuration(jobTrackingConfig, 'job_tracking');
        console.log('Job tracking config saved');
    } catch (error) {
        console.log('Error saving job tracking config:', error);
    }
}

async function trackJobApplicationFromText() {
    const queryBox = document.getElementById('query-box');
    const query = queryBox ? queryBox.value.trim() : '';
    const userId = window.userId || window.user_id;

    if (!userId) {
        showAlert('Please login first.', 'warning');
        return;
    }

    if (!query) {
        showAlert('Please enter text in the query box.', 'warning');
        return;
    }

    const trackJobBtn = document.getElementById('track-job-btn');
    const spinner = document.getElementById('spinner');

    try {
        const response = await window.pywebview.api.track_job_application_from_text(
            userId,
            query
        );

        if (response && response.code === 'OK') {
            showAlert('Job application tracked successfully!', 'success');

            // Fill in the tracking pane fields with response data
            const job = response.job;
            if (job) {
                addJobToTable(job, response.company_name);
            }
        } else {
            showAlert('Failed to track job application.', 'error');
        }
    } catch (error) {
        console.error('Track job failed:', error);
        showAlert('Failed to track job. Please check the console for details.', 'error');
    } finally {
        // Re-enable button
        if (trackJobBtn) {
            trackJobBtn.disabled = false;
            trackJobBtn.textContent = 'Track Job Application';
        }

        // Hide spinner
        if (spinner) {
            spinner.classList.remove('visible');
            document.body.classList.remove('spinner-active');
        }
    }
}

function displayJobsTable(jobs, companyName) {
    const tableContainer = document.getElementById('job-tracking-container');
    const tableBody = document.getElementById('job-table-body');

    if (!tableContainer || !tableBody) return;

    // Clear existing rows
    tableBody.innerHTML = '';

    // Add jobs to table
    jobs.forEach(job => {
        addJobToTable(job, companyName);
    });

    // Show table
    tableContainer.style.display = 'block';
}

function getRowData(row) {
    return {
        company_name: row.querySelector('.company-name').value,
        job_title: row.querySelector('.job-title').value,
        job_url: row.querySelector('.job-url').value,
        job_state: row.querySelector('.state-cell select').value,
        contact_name: row.querySelector('.contact-name').value,
        contact_linkedin: row.querySelector('.contact-linkedin').value,
        contact_email: row.querySelector('.contact-email').value
    };
}

async function trackJobApplicationFromRow(rowData) {
    const userId = window.userId || window.user_id;
    if (!userId) {
        showAlert('Please login first.', 'warning');
        return;
    }

    const jobDto = {
        job_url: rowData.job_url,
        job_title: rowData.job_title,
        job_state: rowData.job_state,
        contact_name: rowData.contact_name || null,
        contact_linkedin: rowData.contact_linkedin || null,
        contact_email: rowData.contact_email || null
    };
    const spinner = document.getElementById('spinner');
    if (spinner) {
        spinner.classList.add('visible');
        document.body.classList.add('spinner-active');
    }

    try {
        const response = await window.pywebview.api.track_job_application(
            userId,
            rowData.company_name,
            jobDto
        );

        if (response && response.code === 'OK') {
            showAlert('Job application tracked successfully!', 'success');
            await saveJobTrackingConfig(rowData);
        } else {
            showAlert('Failed to track job application.', 'error');
        }
    } catch (error) {
        console.error('Track job failed:', error);
        showAlert('Failed to track job. Please check the console for details.', 'error');
    }

    finally {
        // Hide spinner
        if (spinner) {
            spinner.classList.remove('visible');
            document.body.classList.remove('spinner-active');
        }
    }
}

async function viewJobApplicationsFromRow(companyName) {
    const userId = window.userId || window.user_id;
    if (!userId) {
        showAlert('Please login first.', 'warning');
        return;
    }

    const spinner = document.getElementById('spinner');
    if (spinner) {
        spinner.classList.add('visible');
        document.body.classList.add('spinner-active');
    }

    try {
        const response = await window.pywebview.api.get_positions(userId, companyName);
        if (response && response.jobs) {
            displayJobsTable(response.jobs, companyName);
        }
    } catch (error) {
        console.error('Error retrieving jobs:', error);
        showAlert('Failed to retrieve jobs.', 'error');
    } finally {
        // Hide spinner
        if (spinner) {
            spinner.classList.remove('visible');
            document.body.classList.remove('spinner-active');
        }
    }
}
