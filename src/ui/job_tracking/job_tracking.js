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
            await trackJob(getFormData(), true);
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
            fillRowFromUrl();
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

async function trackJob(rowData, isFromBlankRow = false, rowElement = null) {
    const userId = window.userId;
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

    const spinner = document.getElementById('job-spinner');
    if (spinner) {
        spinner.classList.add('visible');
    }

    try {
        const jobTrackingResponse = await window.pywebview.api.track_job(
            userId,
            rowData.company_name,
            jobDto
        );

        if (jobTrackingResponse && jobTrackingResponse.code === 'OK') {
            showAlert('Job application tracked successfully!', 'success');
            if (jobTrackingResponse.job) {
                if (isFromBlankRow) {
                    addJobToTable(jobTrackingResponse.job, rowData.company_name, jobTrackingResponse.company_id);
                    clearForm();
                } else if (rowElement) {
                    updateRow(rowElement, jobTrackingResponse.job);
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
        }
    }
}

async function viewJobApplications(companyName) {
    const userId = window.userId;
    if (!userId) {
        showAlert('Please login first.', 'warning');
        return;
    }

    if (!companyName) {
        showAlert('Please enter a company name.', 'warning');
        return;
    }

    const spinner = document.getElementById('job-spinner');
    if (spinner) {
        spinner.classList.add('visible');
    }

    try {
        const response = await window.pywebview.api.get_tracked_jobs(userId, companyName);
        if (response && response.company) {
            displayJobsTable(response.company);
        } else {
            showAlert(`No jobs found for ${companyName}.`, 'info');
        }
    } catch (error) {
        console.error('Error retrieving jobs:', error);
        showAlert('Failed to retrieve jobs.', 'error');
    } finally {
        if (spinner) {
            spinner.classList.remove('visible');
        }
    }
}

function updateBulkDeleteVisibility() {
    const checkboxes = document.querySelectorAll('.row-checkbox');
    const anyChecked = Array.from(checkboxes).some(cb => cb.checked);
    const bulkDelete = document.getElementById('bulk-delete-container');
    if (bulkDelete) bulkDelete.style.display = anyChecked ? 'block' : 'none';
}

function addJobToTable(job, companyName, companyId) {
    const tableBody = document.getElementById('job-table-body');
    const row = document.createElement('tr');

    if (job.job_id) row.setAttribute('data-job-id', job.job_id);
    if (companyId) row.setAttribute('data-company-id', companyId);

    // Create cells
    const companyCell = document.createElement('td');
    companyCell.className = "align-middle"; // Vertical centering

    // Container to keep checkbox and input aligned
    const companyWrapper = document.createElement('div');
    companyWrapper.className = "d-flex align-items-center gap-2 h-100";

    const selectCheckbox = document.createElement('input');
    selectCheckbox.type = 'checkbox';
    selectCheckbox.className = 'row-checkbox form-check-input mt-0';
    selectCheckbox.addEventListener('change', updateBulkDeleteVisibility);

    const companyInput = document.createElement('input');
    companyInput.type = 'text';
    companyInput.className = 'form-control form-control-sm company-name company-input';
    companyInput.value = companyName || '';
    companyInput.readOnly = true;

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
        if (isReadOnly) input.readOnly = true;
        cell.appendChild(input);
        return cell;
    };

    row.appendChild(companyCell);

    const titleCell = document.createElement('td');
    titleCell.className = "align-middle";
    const titleDiv = document.createElement('div');
    titleDiv.className = 'job-title';
    titleDiv.textContent = job.job_title || '';
    titleDiv.style.cssText = 'word-wrap: break-word; overflow-wrap: break-word; white-space: normal;';
    titleCell.appendChild(titleDiv);
    row.appendChild(titleCell);

    // Job URL as clickable link
    const urlCell = document.createElement('td');
    urlCell.className = "align-middle";
    if (job.job_url) {
        const urlLink = document.createElement('a');
        urlLink.href = job.job_url;
        urlLink.target = '_blank';
        urlLink.textContent = job.job_url;
        urlLink.className = 'text-primary job-url-link';
        urlCell.appendChild(urlLink);
    }
    row.appendChild(urlCell);

    const stateCell = document.createElement('td');
    stateCell.className = 'state-cell align-middle';
    const stateSelectElement = createStateSelect();
    stateCell.appendChild(stateSelectElement);
    row.appendChild(stateCell);

    // Set the select value
    if (job.job_state && stateSelectElement.querySelector(`option[value="${job.job_state}"]`)) {
        stateSelectElement.value = job.job_state;
    }

    row.appendChild(createInputCell(job.update_time, 'date-time', true));

    // Contact LinkedIn as editable input
    row.appendChild(createInputCell(job.contact_linkedin, 'contact-linkedin'));

    row.appendChild(createInputCell(job.contact_name, 'contact-name'));

    // Contact Email as editable input
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
        await trackJob(getRowData(row), false, row);
    });

    viewBtn.addEventListener('click', async (e) => {
        e.preventDefault();
        await viewJobApplications(getRowData(row).company_name);
    });

    tableBody.prepend(row);
}

function updateRow(row, job) {
    const jobTitleDiv = row.querySelector('.job-title');
    if (jobTitleDiv) jobTitleDiv.textContent = job.job_title || '';

    const urlLink = row.querySelector('.job-url-link');
    if (urlLink) {
        urlLink.href = job.job_url || '';
        urlLink.textContent = job.job_url || '';
    }

    const stateSelect = row.querySelector('.state-cell select');
    if (stateSelect) stateSelect.value = job.job_state || '';

    const dateTimeInput = row.querySelector('.date-time');
    if (dateTimeInput) dateTimeInput.value = job.update_time || '';

    const linkedinInput = row.querySelector('.contact-linkedin');
    if (linkedinInput) linkedinInput.value = job.contact_linkedin || '';

    const contactNameInput = row.querySelector('.contact-name');
    if (contactNameInput) contactNameInput.value = job.contact_name || '';

    const emailInput = row.querySelector('.contact-email');
    if (emailInput) emailInput.value = job.contact_email || '';
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
    await trackJob(rowData, isFromBlankRow, isFromBlankRow ? null : targetRow);
}

async function fillRowFromUrl() {
    const activeElement = document.activeElement;
    let targetRow = activeElement?.closest('tr') || document.querySelector('#job-input-body tr');
    if (!targetRow) return;

    const companyInput = targetRow.querySelector('.company-name, #company-name');
    const jobTitleElement = targetRow.querySelector('.job-title, #job_title');
    const jobUrlInput = targetRow.querySelector('.job-url, #job_url');
    const contactLinkedInInput = targetRow.querySelector('.contact-linkedin, #contact_linkedin');
    const contactNameInput = targetRow.querySelector('.contact-name, #contact_name');

    // Check if fields are already filled
    const titleFilled = jobTitleElement?.tagName === 'INPUT' 
        ? jobTitleElement.value 
        : jobTitleElement?.textContent.trim();
    
    if ((companyInput?.value) && titleFilled && (contactNameInput?.value)) {
        return;
    }

    try {
        if (jobUrlInput.value.includes('linkedin.com/jobs')) {
            const result = await window.pywebview.api.extract_job_title_and_company(jobUrlInput.value);
            if (result) {
                if (!companyInput.value) companyInput.value = result.company_name || '';
                
                // Handle job title for both input and div elements
                if (jobTitleElement && !titleFilled) {
                    if (jobTitleElement.tagName === 'INPUT') {
                        jobTitleElement.value = result.job_title || '';
                    } else {
                        jobTitleElement.textContent = result.job_title || '';
                    }
                }
            }
        }
    } catch (error) {
        console.error('Error updating from URLs:', error);
    }

    if (!contactNameInput.value && contactLinkedInInput.value.includes('linkedin.com/in/')) {
        const contactName = getContactNameFromLinkedin(contactLinkedInInput.value);
        if (contactName) contactNameInput.value = contactName;
    }
    if (!companyInput?.value && !jobUrlInput.value.includes('linkedin.com/jobs')) {
        companyInput.value = getCompanyFromUrl(jobUrlInput.value);
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

function displayJobsTable(company) {
    const tableContainer = document.getElementById('job-tracking-container');
    const tableBody = document.getElementById('job-table-body');
    if (!tableContainer || !tableBody) return;
    tableBody.innerHTML = '';

    if (company.tracked_jobs.length === 0) {
        showAlert(`No jobs found for ${company.company_name}`, 'info');
        return;
    }
    jobs = company.tracked_jobs
    let companyName = company.company_name;
    let companyId = company.company_id;
    jobs.forEach(job => addJobToTable(job, companyName, companyId));
    tableContainer.style.display = 'block';
}

function getRowData(row) {
    const find = (sel) => row.querySelector(sel)?.value.trim() || '';
    return {
        job_id: row.getAttribute('data-job-id'), // Get the ID
        company_id: row.getAttribute('data-company-id'),
        company_name: find('.company-name') || find('#company-name'),
        job_title: row.querySelector('.job-title')?.textContent.trim() || find('#job_title'),
        job_url: row.querySelector('.job-url-link')?.textContent.trim() || find('.job-url') || find('#job_url'),
        job_state: find('.state-cell select') || find('#job_state'),
        contact_name: find('.contact-name') || find('#contact_name'),
        contact_linkedin: find('.contact-linkedin') || find('#contact_linkedin'),
        contact_email: find('.contact-email') || find('#contact_email'),
        date_time: find('.date-time') || find('#job_date_time')
    };
}

async function bulkDeleteSelectedRows() {
    const userId = window.userId;
    if (!userId) return;

    console.log("userId")

    const checkboxes = document.querySelectorAll('.row-checkbox:checked');
    if (checkboxes.length === 0) return;

    const companiesJobs = {};
    checkboxes.forEach(cb => {
        const row = cb.closest('tr');
        const rowData = getRowData(row);
        if (!companiesJobs[rowData.company_name]) companiesJobs[rowData.company_name] =
            { company_id: rowData.company_id, company_name: rowData.company_name, tracked_jobs: [] };

        companiesJobs[rowData.company_name].tracked_jobs.push({
            job_id: rowData.job_id,
            job_url: rowData.job_url,
            job_title: rowData.job_title,
            job_state: rowData.job_state,
            contact_name: rowData.contact_name,
            contact_linkedin: rowData.contact_linkedin,
            contact_email: rowData.contact_email
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