// Job Tracking JavaScript - Bootstrap Compatible

// Element ID constants
const ELEMENT_IDS = {
    COMPANY_NAME: 'company-name',
    JOB_TITLE: 'job_title',
    JOB_URL: 'job_url',
    CONTACT_NAME: 'contact_name',
    CONTACT_LINKEDIN: 'contact_linkedin',
    CONTACT_EMAIL: 'contact_email',
    JOB_STATE: 'job_state',
    UPDATE_TIME: 'update-time'
};

async function initJobTracking() {
    console.log('Initializing Job Tracking...');

    await loadJobApplicationStates();
    await loadJobTrackingConfig();
    await initJobTrackingEventListeners();
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

async function loadJobApplicationStates() {
    try {
        const states = await window.pywebview.api.get_job_application_states();
        const stateSelect = document.getElementById(ELEMENT_IDS.JOB_STATE);

        if (!stateSelect) {
            console.error('job_state element not found');
            return;
        }

        stateSelect.innerHTML = '';

        if (states && Array.isArray(states)) {
            states.forEach(state => {
                const option = document.createElement('option');
                option.value = state;
                option.textContent = getStateLabel(state);
                stateSelect.appendChild(option);
            });
            console.log(`Loaded ${states.length} job application states`);
        } else {
            console.warn('No job application states returned');
        }
    } catch (error) {
        console.error('Error loading job application states:', error);
    }
}

async function loadJobTrackingConfig() {
    
        // Populate form fields
        const companyName = document.getElementById(ELEMENT_IDS.COMPANY_NAME);
        const positionTitle = document.getElementById(ELEMENT_IDS.JOB_TITLE);
        const positionUrl = document.getElementById(ELEMENT_IDS.JOB_URL);
        const contactName = document.getElementById(ELEMENT_IDS.CONTACT_NAME);
        const contactLinkedin = document.getElementById(ELEMENT_IDS.CONTACT_LINKEDIN);
        const contactEmail = document.getElementById(ELEMENT_IDS.CONTACT_EMAIL);
        const jobState = document.getElementById(ELEMENT_IDS.JOB_STATE);

        if (companyName) companyName.value = config.job_tracking.company_name || '';
        if (positionTitle) positionTitle.value = config.job_tracking.job_title || '';
        if (positionUrl) positionUrl.value = config.job_tracking.job_url || '';
        if (contactName) contactName.value = config.job_tracking.contact_name || '';
        if (contactLinkedin) contactLinkedin.value = config.job_tracking.contact_linkedin || '';
        if (contactEmail) contactEmail.value = config.job_tracking.contact_email || '';
        if (jobState) jobState.value = config.job_tracking.job_state || '';

        console.log('Job tracking config loaded successfully');
}

async function saveJobTrackingConfig() {
    try {
        const jobTrackingConfig = {
            company_name: document.getElementById(ELEMENT_IDS.COMPANY_NAME)?.value || '',
            job_title: document.getElementById(ELEMENT_IDS.JOB_TITLE)?.value || '',
            job_url: document.getElementById(ELEMENT_IDS.JOB_URL)?.value || '',
            contact_name: document.getElementById(ELEMENT_IDS.CONTACT_NAME)?.value || '',
            contact_linkedin: document.getElementById(ELEMENT_IDS.CONTACT_LINKEDIN)?.value || '',
            contact_email: document.getElementById(ELEMENT_IDS.CONTACT_EMAIL)?.value || '',
            job_state: document.getElementById(ELEMENT_IDS.JOB_STATE)?.value || ''
        };

        await window.pywebview.api.save_configuration(jobTrackingConfig, 'job_tracking');
        console.log('Job tracking config saved');
    } catch (error) {
        console.log('Error saving job tracking config:', error);
    }
}

async function initJobTrackingEventListeners() {
    const companyNameElement = document.getElementById(ELEMENT_IDS.COMPANY_NAME);
    const jobTitleElement = document.getElementById(ELEMENT_IDS.JOB_TITLE);
    const jobUrlElement = document.getElementById(ELEMENT_IDS.JOB_URL);
    const contactNameElement = document.getElementById(ELEMENT_IDS.CONTACT_NAME);
    const contactLinkedinElement = document.getElementById(ELEMENT_IDS.CONTACT_LINKEDIN);
    const contactEmailElement = document.getElementById(ELEMENT_IDS.CONTACT_EMAIL);
    const jobStateElement = document.getElementById(ELEMENT_IDS.JOB_STATE);
    const trackJobBtn = document.getElementById('track-job-btn');
    const viewJobsBtn = document.getElementById('view-jobs-btn');

    if (!trackJobBtn) {
        console.error('Track job button not found');
        return;
    }

    // Save config on input change with debouncing
    const debounce = (func, delay) => {
        let timeoutId;
        return function (...args) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => func.apply(this, args), delay);
        };
    };

    const debouncedSave = debounce(saveJobTrackingConfig, 500);

    if (companyNameElement) {
        companyNameElement.addEventListener('input', debouncedSave);
    }

    if (jobTitleElement) {
        jobTitleElement.addEventListener('input', debouncedSave);
    }

    if (jobUrlElement) {
        jobUrlElement.addEventListener('input', debouncedSave);
    }

    if (contactNameElement) {
        contactNameElement.addEventListener('input', debouncedSave);
    }

    if (contactLinkedinElement) {
        contactLinkedinElement.addEventListener('input', debouncedSave);
    }

    if (contactEmailElement) {
        contactEmailElement.addEventListener('input', debouncedSave);
    }

    if (jobStateElement) {
        jobStateElement.addEventListener('change', debouncedSave);
    }

    // Track job button click
    trackJobBtn.addEventListener('click', async () => {
        await trackJobApplication();
    });

    if (viewJobsBtn) {
        viewJobsBtn.addEventListener('click', async () => {
            await viewJobApplications();
        });
    }

    // Add keyboard shortcut for Ctrl+Alt+M
    document.addEventListener('keydown', function (event) {
        if (event.ctrlKey && event.altKey && event.key === 'm') {
            event.preventDefault();
            trackJobApplicationFromText();
        }
    });
}

async function viewJobApplications() {
    const companyNameInput = document.getElementById(ELEMENT_IDS.COMPANY_NAME);
    const userId = window.userId || window.user_id;
    if (!userId) {
        showAlert('Please login first.', 'warning');
        return;
    }
    if (!companyNameInput) {
        console.error('Fill in company name for getting job infomration');
        return;
    }
    const companyName = companyNameInput.value.trim();
    const responseBox = document.getElementById('response-box');
    const spinner = document.getElementById('spinner');
    const viewJobsBtn = document.getElementById('view-jobs-btn');

    if (viewJobsBtn) viewJobsBtn.disabled = true;
    if (spinner) {
        spinner.classList.add('visible');
        document.body.classList.add('spinner-active');
    }

    try {
        const response = await window.pywebview.api.get_positions(userId, companyName);

        if (response && response.jobs) {
            displayJobsTable(response.jobs);
        } else {
            const responseElem = document.createElement('div');
            responseElem.className = 'llm-response';
            responseElem.textContent = JSON.stringify(response.jobs, null, 2);
            responseBox.appendChild(responseElem);
            responseBox.scrollTop = responseBox.scrollHeight;
        }
    } catch (error) {
        console.error('Error retrieving jobs:', error);
        showAlert('Failed to retrieve jobs.', 'error');
    } finally {
        if (viewJobsBtn) viewJobsBtn.disabled = false;
        if (spinner) {
            spinner.classList.remove('visible');
            document.body.classList.remove('spinner-active');
        }
    }
}

async function trackJobApplication() {
    const companyNameInput = document.getElementById(ELEMENT_IDS.COMPANY_NAME);
    const jobTitleInput = document.getElementById(ELEMENT_IDS.JOB_TITLE);
    const jobUrlInput = document.getElementById(ELEMENT_IDS.JOB_URL);
    const contactNameInput = document.getElementById(ELEMENT_IDS.CONTACT_NAME);
    const contactLinkedinInput = document.getElementById(ELEMENT_IDS.CONTACT_LINKEDIN);
    const contactEmailInput = document.getElementById(ELEMENT_IDS.CONTACT_EMAIL);
    const jobStateElement = document.getElementById(ELEMENT_IDS.JOB_STATE);

    if (!companyNameInput || !jobUrlInput || !jobTitleInput || !jobStateElement) {
        console.error('Required job tracking elements not found');
        return;
    }

    const companyName = companyNameInput.value.trim();
    const jobUrl = jobUrlInput.value.trim();
    const jobTitle = jobTitleInput.value.trim();
    const contactName = contactNameInput ? contactNameInput.value.trim() : '';
    const contactLinkedin = contactLinkedinInput ? contactLinkedinInput.value.trim() : '';
    const contactEmail = contactEmailInput ? contactEmailInput.value.trim() : '';
    const jobState = jobStateElement.value;
    const trackJobBtn = document.getElementById('track-job-btn');
    // Validation
    if (!companyName || !jobUrl) {
        showAlert('Please fill in Company Name and Position URL.', 'warning');
        if (!companyName) companyNameInput.focus();
        else jobUrlInput.focus();
        return;
    }

    if (!jobState) {
        showAlert('Please select a Job State.', 'warning');
        jobStateElement.focus();
        return;
    }

    const userId = window.userId || window.user_id;
    if (!userId) {
        showAlert('Please login first.', 'warning');
        return;
    }

    // Disable button during submission
    if (trackJobBtn) {
        trackJobBtn.disabled = true;
        trackJobBtn.textContent = 'Tracking...';
    }

    const spinner = document.getElementById('spinner');
    if (spinner) {
        spinner.classList.add('visible');
        document.body.classList.add('spinner-active');
    }
    
        const jobDto = {
            job_url: jobUrl,
            job_title: jobTitle,
            job_state: jobState,
            contact_name: contactName || null,
            contact_linkedin: contactLinkedin || null,
            contact_email: contactEmail || null
        };

    try {
     

        const response = await window.pywebview.api.track_job_application(
            userId,
            companyName,
            jobDto
        );

        if (response && response.code === 'OK') {
            showAlert('Job application tracked successfully!', 'success');
            
            // Fill in the tracking pane fields with response data
            const job = response.job;
            if (job) {
                addJobToTable(job);
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
                addJobToTable(job);
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

function displayJobsTable(jobs) {
    const tableContainer = document.getElementById('job-tracking-container');
    const tableBody = document.getElementById('job-table-body');
    
    if (!tableContainer || !tableBody) return;
    
    // Clear existing rows
    tableBody.innerHTML = '';
    
    // Add jobs to table
    jobs.forEach(job => {
        addJobToTable(job);
    });
    
    // Show table
    tableContainer.style.display = 'block';
}

function addJobToTable(job) {
    const tableBody = document.getElementById('job-table-body');
    const row = document.createElement('tr');
    
    // Get options from the main state selector
    const mainStateSelect = document.getElementById(ELEMENT_IDS.JOB_STATE);
    const stateOptions = mainStateSelect ? mainStateSelect.innerHTML : '';

    row.innerHTML = `
        <td><input type="text" class="form-control form-control-sm" value="${job.company_name || ''}"></td>
        <td><input type="text" class="form-control form-control-sm" value="${job.job_title || ''}"></td>
        <td><input type="text" class="form-control form-control-sm" value="${job.job_url || ''}"></td>
        <td><input type="text" class="form-control form-control-sm" value="${job.contact_name || ''}"></td>
        <td><input type="text" class="form-control form-control-sm" value="${job.contact_email || ''}"></td>
        <td><input type="text" class="form-control form-control-sm" value="${job.contact_linkedin || ''}"></td>
        <td><select class="form-select form-select-sm">${stateOptions}</select></td>
        <td><button class="btn btn-primary btn-sm w-100">Save</button></td>
    `;
    
    const select = row.querySelector('select');
    if (select && job.job_state) select.value = job.job_state;

    // Insert at the top of the data rows
    tableBody.insertBefore(row, tableBody.firstChild);
}
