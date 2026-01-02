let states = [];

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
        showAlert('Failed to track job.', 'error');
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
        } else {
            showAlert(`No jobs found for ${companyName}.`, 'info');
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
    companyCell.className = "align-middle"; // Vertical centering

    // Container to keep checkbox and input aligned
    const companyWrapper = document.createElement('div');
    companyWrapper.className = "d-flex align-items-center gap-2";

    const selectCheckbox = document.createElement('input');
    selectCheckbox.type = 'checkbox';
    selectCheckbox.className = 'row-checkbox form-check-input mt-0';
    selectCheckbox.addEventListener('change', updateBulkDeleteVisibility);

    const companyInput = document.createElement('input');
    companyInput.type = 'text';
    companyInput.className = 'form-control form-control-sm company-name company-input';
    companyInput.value = companyName || '';
    companyInput.readOnly = true; // CHANGE 1: Readonly

    companyWrapper.appendChild(selectCheckbox);
    companyWrapper.appendChild(companyInput);
    companyCell.appendChild(companyWrapper);

    // Helper for cells
    const createInputCell = (value, className, isReadOnly = false) => {
        const cell = document.createElement('td');
        cell.className = "align-middle";
        const input = document.createElement('input');
        input.type = 'text';
        input.className = `form-control form-control-sm ${className}`;
        input.value = value || '';
        if (isReadOnly) input.readOnly = true; // CHANGE 1: Readonly
        cell.appendChild(input);
        return cell;
    };

    row.appendChild(companyCell);
    row.appendChild(createInputCell(job.job_title, 'job-title', true)); // CHANGE 1: Readonly
    row.appendChild(createInputCell(job.job_url, 'job-url', true));     // CHANGE 1: Readonly

    const stateCell = document.createElement('td');
    stateCell.className = 'state-cell align-middle';
    const stateSelectElement = createStateSelect();
    stateCell.appendChild(stateSelectElement);
    row.appendChild(stateCell);

    // Set the select value
    if (job.job_state && stateSelectElement.querySelector(`option[value="${job.job_state}"]`)) {
        stateSelectElement.value = job.job_state;
    }

    row.appendChild(createInputCell(formatDateTime(job.update_time), 'date-time', true));
    row.appendChild(createInputCell(job.contact_linkedin, 'contact-linkedin'));
    row.appendChild(createInputCell(job.contact_name, 'contact-name'));
    row.appendChild(createInputCell(job.contact_email, 'contact-email'));

    const actionCell = document.createElement('td');
    actionCell.className = "align-middle";
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

    // Add event listeners
    trackBtn.addEventListener('click', async (e) => {
        e.preventDefault();
        await trackJobApplication(getRowData(row), false, row);
    });

    viewBtn.addEventListener('click', async (e) => {
        e.preventDefault();
        await viewJobApplications(getRowData(row).company_name);
    });

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
    const activeElement = document.activeElement;
    let targetRow = activeElement?.closest('tr') || document.querySelector('#job-input-body tr');
    if (!targetRow) return;
    const rowData = getRowData(targetRow);
    await viewJobApplications(rowData.company_name);
}

async function trackCurrentRow() {
    const activeElement = document.activeElement;
    let targetRow = activeElement?.closest('tr') || document.querySelector('#job-input-body tr');
    if (!targetRow) return;
    const isFromBlankRow = targetRow.parentElement.id === 'job-input-body';
    const rowData = getRowData(targetRow);
    await trackJobApplication(rowData, isFromBlankRow, isFromBlankRow ? null : targetRow);
}

async function trackFromUrl() {
    const activeElement = document.activeElement;
    let targetRow = activeElement?.closest('tr') || document.querySelector('#job-input-body tr');
    if (!targetRow) return;

    const companyInput = targetRow.querySelector('.company-name, #company-name');
    const jobTitleInput = targetRow.querySelector('.job-title, #job_title');
    const jobUrlInput = targetRow.querySelector('.job-url, #job_url');
    const contactLinkedInInput = targetRow.querySelector('.contact-linkedin, #contact_linkedin');
    const contactNameInput = targetRow.querySelector('.contact-name, #contact_name');

    try {
        if (jobUrlInput.value.includes('linkedin.com/jobs')) {
            const result = await window.pywebview.api.extract_job_title_and_company(jobUrlInput.value);
            if (result) {
                if (!companyInput.value) companyInput.value = result.company_name || '';
                if (!jobTitleInput.value) jobTitleInput.value = result.job_title || '';
            }
        }
        if (!contactNameInput.value && contactLinkedInInput.value.includes('linkedin.com/in/')) {
            const contactName = getContactNameFromLinkedin(contactLinkedInInput.value);
            if (contactName) contactNameInput.value = contactName;
        }
    } catch (error) {
        console.error('Error updating from URLs:', error);
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
        day: '2-digit', month: '2-digit', year: 'numeric',
        hour: '2-digit', minute: '2-digit', hour12: false
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
    ['company-name', 'job_title', 'job_url', 'contact_name', 'contact_linkedin', 'contact_email', 'job_date_time']
        .forEach(id => document.getElementById(id).value = '');
    document.getElementById('job_state').selectedIndex = 0;
}

function displayJobsTable(jobs, companyName) {
    const tableContainer = document.getElementById('job-tracking-container');
    const tableBody = document.getElementById('job-table-body');
    if (!tableContainer || !tableBody) return;
    tableBody.innerHTML = '';
    jobs.forEach(job => addJobToTable(job, companyName));
    tableContainer.style.display = 'block';
}

function getRowData(row) {
    const find = (sel) => row.querySelector(sel)?.value.trim() || '';
    return {
        company_name: find('.company-name') || find('#company-name'),
        job_title: find('.job-title') || find('#job_title'),
        job_url: find('.job-url') || find('#job_url'),
        job_state: find('.state-cell select') || find('#job_state'),
        contact_name: find('.contact-name') || find('#contact_name'),
        contact_linkedin: find('.contact-linkedin') || find('#contact_linkedin'),
        contact_email: find('.contact-email') || find('#contact_email'),
        date_time: find('.date-time') || find('#job_date_time')
    };
}

async function bulkDeleteSelectedRows() {
    const userId = window.userId || window.user_id;
    if (!userId) return;

    const checkboxes = document.querySelectorAll('.row-checkbox:checked');
    if (checkboxes.length === 0) return;

    const companiesJobs = {};
    checkboxes.forEach(cb => {
        const row = cb.closest('tr');
        const d = getRowData(row);
        if (!companiesJobs[d.company_name]) companiesJobs[d.company_name] = { company_name: d.company_name, tracked_jobs: [] };
        companiesJobs[d.company_name].tracked_jobs.push({
            job_url: d.job_url, job_title: d.job_title, job_state: d.job_state,
            contact_name: d.contact_name, contact_linkedin: d.contact_linkedin, contact_email: d.contact_email
        });
    });

    try {
        const response = await window.pywebview.api.delete_tracked_jobs(userId, Object.values(companiesJobs));
        if (response?.success) {
            checkboxes.forEach(cb => cb.closest('tr').remove());
            updateBulkDeleteVisibility();
            showAlert('Deleted successfully', 'success');
        }
    } catch (error) {
        console.error(error);
    }
}