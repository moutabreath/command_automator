states = []
async function initJobTracking() {
    console.log('Initializing Job Tracking...');
    states = await window.pywebview.api.get_job_application_states();

    populateStateSelect(document.getElementById('job_state'));

    // Add event listeners for main form buttons
    const trackJobBtn = document.getElementById('track-job-btn');
    const viewJobsBtn = document.getElementById('view-jobs-btn');

    if (trackJobBtn) {
        trackJobBtn.addEventListener('click', async () => {
            await trackJobApplication(getFormData(), true);
        });
    }

    if (viewJobsBtn) {
        viewJobsBtn.addEventListener('click', async () => {
            const formData = getFormData();
            await viewJobApplications(formData.company_name);
        });
    }

    // Add keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.altKey && e.key === 'm') {
            e.preventDefault();
            trackFromUrl();
        }
        if (e.ctrlKey && e.altKey && e.key === 't') {
            e.preventDefault();
            trackCurrentRow();
        }
        if (e.ctrlKey && e.altKey && e.key === 'v') {
            e.preventDefault();
            viewCurrentRow();
        }
    });

    // Add bulk delete functionality
    const bulkDeleteBtn = document.getElementById('bulk-delete-btn');
    if (bulkDeleteBtn) {
        bulkDeleteBtn.addEventListener('click', async () => {
            await bulkDeleteSelectedRows();
        });
    }
}

async function trackJobApplication(rowData, isFromBlankRow = false, rowElement = null) {
    const userId = window.userId || window.user_id;
    if (!userId) {
        showAlert('Please login first.', 'warning');
        return;
    }

    if (!rowData.company_name || !rowData.job_url) {
        showAlert('Please fill in Company Name and Job URL.', 'warning');
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
            if (response.job) {
                if (isFromBlankRow) {
                    addJobToTable(response.job, rowData.company_name);
                    clearForm();
                } else if (rowElement) {
                    updateRow(rowElement, response.job);
                }
            }
        } else {
            showAlert('Failed to track job application.', 'error');
        }
    } catch (error) {
        console.error('Track job failed:', error);
        showAlert('Failed to track job. Please check the console for details.', 'error');
    } finally {
        if (spinner) {
            spinner.classList.remove('visible');
            document.body.classList.remove('spinner-active');
        }
    }
}

async function viewJobApplications(companyName) {
    const userId = window.userId || window.user_id;
    if (!userId) {
        showAlert('Please login first.', 'warning');
        return;
    }

    if (!companyName) {
        showAlert('Please enter a company name.', 'warning');
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
        else {
            showAlert('No jobs found for the company {companyName}.', 'info');
        }
    } catch (error) {
        console.error('Error retrieving jobs:', error);
        showAlert('Failed to retrieve jobs.', 'error');
    } finally {
        if (spinner) {
            spinner.classList.remove('visible');
            document.body.classList.remove('spinner-active');
        }
    }
}


function updateBulkDeleteVisibility() {
    const checkboxes = document.querySelectorAll('.row-checkbox');
    const anyChecked = Array.from(checkboxes).some(cb => cb.checked);
    const bulkDelete = document.getElementById('bulk-delete-container');
    if (bulkDelete) bulkDelete.style.display = anyChecked ? 'block' : 'none';
}

function addJobToTable(job, companyName) {
    const tableBody = document.getElementById('job-table-body');
    const row = document.createElement('tr');

    // Create cells
    const companyCell = document.createElement('td');
    const selectCheckbox = document.createElement('input');
    selectCheckbox.type = 'checkbox';
    selectCheckbox.className = 'row-checkbox';
    selectCheckbox.addEventListener('change', updateBulkDeleteVisibility);
    const companyInput = document.createElement('input');
    companyInput.type = 'text';
    companyInput.className = 'form-control form-control-sm company-name company-input';
    companyInput.value = companyName || '';
    companyCell.appendChild(selectCheckbox);
    companyCell.appendChild(companyInput);

    const createInputCell = (value, className) => {
        const cell = document.createElement('td');
        const input = document.createElement('input');
        input.type = 'text';
        input.className = `form-control form-control-sm ${className}`;
        input.value = value || '';
        cell.appendChild(input);
        return cell;
    };

    row.appendChild(companyCell);
    row.appendChild(createInputCell(job.job_title, 'job-title'));
    row.appendChild(createInputCell(job.job_url, 'job-url'));

    const newStateCell = document.createElement('td');
    newStateCell.className = 'state-cell';
    row.appendChild(newStateCell);

    row.appendChild(createInputCell(formatDateTime(job.update_time), 'date-time'));

    row.appendChild(createInputCell(job.contact_linkedin, 'contact-linkedin'));
    row.appendChild(createInputCell(job.contact_name, 'contact-name'));
    row.appendChild(createInputCell(job.contact_email, 'contact-email'));

    const actionCell = document.createElement('td');
    const actionDiv = document.createElement('div');
    actionDiv.className = 'd-flex gap-2';
    const trackBtn = document.createElement('button');
    trackBtn.className = 'btn btn-primary btn-sm w-100 track-job-row-btn';
    trackBtn.textContent = 'Track';

    const viewBtn = document.createElement('button');
    viewBtn.className = 'btn btn-secondary btn-sm w-100 view-jobs-row-btn';
    viewBtn.textContent = 'View';
    actionDiv.appendChild(trackBtn);
    actionDiv.appendChild(viewBtn);
    actionCell.appendChild(actionDiv);
    row.appendChild(actionCell);

    // Create and insert the select element
    const stateSelectElement = createStateSelect();
    const stateCell = row.querySelector('.state-cell');
    stateCell.appendChild(stateSelectElement);

    // Set the select value
    if (job.job_state && stateSelectElement.querySelector(`option[value="${job.job_state}"]`)) {
        stateSelectElement.value = job.job_state;
    }

    // Add event listeners
    const deleteBtn = row.querySelector('.delete-row');

    if (trackBtn) {
        trackBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            await trackJobApplication(getRowData(row), false, row);
   
        });
    }

    if (viewBtn) {
        viewBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            await viewJobApplications(getRowData(row).company_name);
        });
    }

    tableBody.prepend(row);
}

function updateRow(row, job) {
    const jobTitleInput = row.querySelector('.job-title');
    if (jobTitleInput) jobTitleInput.value = job.job_title || '';

    const jobUrlInput = row.querySelector('.job-url');
    if (jobUrlInput) jobUrlInput.value = job.job_url || '';

    const stateSelect = row.querySelector('.state-cell select');
    if (stateSelect) stateSelect.value = job.job_state || '';

    const dateTimeInput = row.querySelector('.date-time');
    if (dateTimeInput) dateTimeInput.value = formatDateTime(job.update_time) || '';

    const contactLinkedInInput = row.querySelector('.contact-linkedin');
    if (contactLinkedInInput) contactLinkedInInput.value = job.contact_linkedin || '';

    const contactNameInput = row.querySelector('.contact-name');
    if (contactNameInput) contactNameInput.value = job.contact_name || '';

    const contactEmailInput = row.querySelector('.contact-email');
    if (contactEmailInput) contactEmailInput.value = job.contact_email || '';
}



async function viewCurrentRow() {
    try {
        // Find currently focused element or use blank form
        const activeElement = document.activeElement;
        let targetRow = null;

        if (activeElement && activeElement.closest('tr')) {
            // Use the row containing the focused element
            targetRow = activeElement.closest('tr');
        } else {
            // Use the blank form row
            targetRow = document.querySelector('#job-input-body tr');
        }

        if (!targetRow) return;

        // Get row data and view applications
        const rowData = getRowData(targetRow) || getFormData();
        await viewJobApplications(rowData.company_name);
    } catch (error) {
        console.error('Error viewing current row applications:', error);
        showAlert('Failed to view job applications', 'error');
    }
}
async function trackCurrentRow() {
    try {
        // Find currently focused element or use blank form
        const activeElement = document.activeElement;
        let targetRow = null;

        if (activeElement && activeElement.closest('tr')) {
            targetRow = activeElement.closest('tr');
        } else {
            targetRow = document.querySelector('#job-input-body tr');
        }

        if (!targetRow) return;

        const isFromBlankRow = targetRow.parentElement.id === 'job-input-body';

        // Get row data and track it
        const rowData = getRowData(targetRow);
        await trackJobApplication(rowData, isFromBlankRow, isFromBlankRow ? null : targetRow);
    } catch (error) {
        console.error('Error tracking current row:', error);
        showAlert('Failed to track job application', 'error');
    }
}

async function trackFromUrl() {
    try {
        // Find currently focused element or use blank form
        const activeElement = document.activeElement;
        let targetRow = null;

        if (activeElement && activeElement.closest('tr')) {
            // Use the row containing the focused element
            targetRow = activeElement.closest('tr');
        } else {
            // Use the blank form row
            targetRow = document.querySelector('#job-input-body tr');
        }

        if (!targetRow) return;

        const companyInput = targetRow.querySelector('.company-name, #company-name');
        const jobTitleInput = targetRow.querySelector('.job-title, #job_title');
        const jobUrlInput = targetRow.querySelector('.job-url, #job_url');
        const contactNameInput = targetRow.querySelector('.contact-name, #contact_name');
        const contactLinkedInInput = targetRow.querySelector('.contact-linkedin, #contact_linkedin');

        // 1.1 Fill company name from LinkedIn URL
        if (!companyInput.value && jobUrlInput.value && jobUrlInput.value.includes('linkedin.com/jobs')) {
            const result = await window.pywebview.api.extract_job_title_and_company(jobUrlInput.value);
            if (result && result.company_name) {
                companyInput.value = result.company_name;
            }
        }

        // 1.2 Extract name from LinkedIn profile URL
        if (!contactNameInput.value && contactLinkedInInput.value && contactLinkedInInput.value.includes('linkedin.com/in/')) {
            const contactName = getContactNameFromLinkedin(contactLinkedInInput.value);
            if (contactName) {
                contactNameInput.value = contactName;
            }
        }

        // 1.3 Fill job title from LinkedIn URL
        if (!jobTitleInput.value && jobUrlInput.value && jobUrlInput.value.includes('linkedin.com/jobs')) {
            const result = await window.pywebview.api.extract_job_title_and_company(jobUrlInput.value);
            if (result && result.job_title) {
                jobTitleInput.value = result.job_title;
            }
        }
    } catch (error) {
        console.error('Error updating from URLs:', error);
        showAlert('Failed to update job details', 'error');
    }
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


function formatDateTime(dateTimeString) {
    if (!dateTimeString) return '';
    return new Date(dateTimeString).toLocaleString('en-GB', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
    });
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

function getFormData() {
    return {
        company_name: document.getElementById('company-name').value.trim(),
        job_title: document.getElementById('job_title').value.trim(),
        job_url: document.getElementById('job_url').value.trim(),
        job_state: document.getElementById('job_state').value,
        contact_name: document.getElementById('contact_name').value.trim(),
        date_time: document.getElementById('job_date_time').value.trim(),
        contact_linkedin: document.getElementById('contact_linkedin').value.trim(),
        contact_email: document.getElementById('contact_email').value.trim()
    };
}

function clearForm() {
    document.getElementById('company-name').value = '';
    document.getElementById('job_title').value = '';
    document.getElementById('job_url').value = '';
    document.getElementById('contact_name').value = '';
    document.getElementById('contact_linkedin').value = '';
    document.getElementById('contact_email').value = '';
    document.getElementById('job_date_time').value = '';
    document.getElementById('job_state').selectedIndex = 0;
}

async function trackJobApplicationFromText() {
    const queryBox = document.getElementById('query-box');
    const text = queryBox ? queryBox.value.trim() : '';
    const userId = window.userId || window.user_id;

    if (!userId) {
        showAlert('Please login first.', 'warning');
        return;
    }

    if (!text) {
        showAlert('Please enter text in the query box.', 'warning');
        return;
    }

    try {
        const result = await trackPositionsFromText(userId, text);

        if (result.job && result.company_name) {
            addJobToTable(result.job, result.company_name);
            showAlert('Job parsed and added to table!', 'success');
        } else {
            showAlert('Failed to parse job from text.', 'error');
        }
    } catch (error) {
        console.error('Track from text failed:', error);
        showAlert('Failed to parse job from text.', 'error');
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
        company_name: (row.querySelector('.company-name') || row.querySelector('#company-name'))?.value || '',
        job_title: (row.querySelector('.job-title') || row.querySelector('#job_title'))?.value || '',
        job_url: (row.querySelector('.job-url') || row.querySelector('#job_url'))?.value || '',
        job_state: (row.querySelector('.state-cell select') || row.querySelector('#job_state'))?.value || '',
        contact_name: (row.querySelector('.contact-name') || row.querySelector('#contact_name'))?.value || '',
        contact_linkedin: (row.querySelector('.contact-linkedin') || row.querySelector('#contact_linkedin'))?.value || '',
        contact_email: (row.querySelector('.contact-email') || row.querySelector('#contact_email'))?.value || '',
        date_time: (row.querySelector('.date-time') || row.querySelector('#job_date_time'))?.value || ''
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

async function bulkDeleteSelectedRows() {
    const userId = window.userId || window.user_id;
    if (!userId) {
        showAlert('Please login first.', 'warning');
        return;
    }

    const checkboxes = document.querySelectorAll('.row-checkbox:checked');
    if (checkboxes.length === 0) {
        showAlert('No rows selected for deletion.', 'warning');
        return;
    }

    // Group jobs by company
    const companiesJobs = {};
    checkboxes.forEach(cb => {
        const row = cb.closest('tr');
        const rowData = getRowData(row);
        const jobDto = {
            job_url: rowData.job_url,
            job_title: rowData.job_title,
            job_state: rowData.job_state,
            contact_name: rowData.contact_name || null,
            contact_linkedin: rowData.contact_linkedin || null,
            contact_email: rowData.contact_email || null
        };

        if (!companiesJobs[rowData.company_name]) {
            companiesJobs[rowData.company_name] = { company_name: rowData.company_name, tracked_jobs: [] };
        }
        companiesJobs[rowData.company_name].tracked_jobs.push(jobDto);
    });

    const companiesJobsList = Object.values(companiesJobs);

    const spinner = document.getElementById('spinner');
    if (spinner) {
        spinner.classList.add('visible');
        document.body.classList.add('spinner-active');
    }

    try {
        const response = await window.pywebview.api.delete_tracked_jobs(userId, companiesJobsList);
        if (response && response['success']  === true) {
            showAlert('Selected jobs deleted successfully!', 'success');
            checkboxes.forEach(cb => cb.closest('tr').remove());
            updateBulkDeleteVisibility();
        } else {
            showAlert('Failed to delete selected jobs.', 'error');
        }
    } catch (error) {
        console.error('Bulk delete failed:', error);
        showAlert('Failed to delete selected jobs. Please check the console for details.', 'error');
    } finally {
        if (spinner) {
            spinner.classList.remove('visible');
            document.body.classList.remove('spinner-active');
        }
    }
}
