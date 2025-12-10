// Job Tracking JavaScript - Bootstrap Compatible

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
        const stateSelect = document.getElementById('job-state');
        
        if (!stateSelect) {
            console.error('job-state element not found');
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
    try {
        let jobTrackingConfig = await window.pywebview.api.load_job_tracking_configuration();
        
        // Check if config is empty or invalid
        if (!jobTrackingConfig || jobTrackingConfig === '' || jobTrackingConfig === ' ') {
            console.log('No job tracking config found');
            return;
        }

        // Populate form fields
        const companyName = document.getElementById('company-name');
        const positionTitle = document.getElementById('position-title');
        const positionUrl = document.getElementById('position-url');
        const contactPerson = document.getElementById('contact-person');

        if (companyName) companyName.value = jobTrackingConfig.company_name || '';
        if (positionTitle) positionTitle.value = jobTrackingConfig.position_title || '';
        if (positionUrl) positionUrl.value = jobTrackingConfig.position_url || '';
        if (contactPerson) contactPerson.value = jobTrackingConfig.contact_person || '';

        console.log('Job tracking config loaded successfully');
    } catch (error) {
        console.log('Error loading job tracking config:', error);
    }
}

async function saveJobTrackingConfig() {
    try {
        const jobTrackingConfig = {
            company_name: document.getElementById('company-name')?.value || '',
            position_title: document.getElementById('position-title')?.value || '',
            position_url: document.getElementById('position-url')?.value || '',
            contact_person: document.getElementById('contact-person')?.value || ''
        };

        await window.pywebview.api.save_job_tracking_configuration(jobTrackingConfig);
        console.log('Job tracking config saved');
    } catch (error) {
        console.log('Error saving job tracking config:', error);
    }
}

async function initJobTrackingEventListeners() {
    const companyName = document.getElementById('company-name');
    const positionTitle = document.getElementById('position-title');
    const positionUrl = document.getElementById('position-url');
    const contactPerson = document.getElementById('contact-person');
    const trackJobBtn = document.getElementById('track-job-btn');

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

    if (companyName) {
        companyName.addEventListener('input', debouncedSave);
    }

    if (positionTitle) {
        positionTitle.addEventListener('input', debouncedSave);
    }

    if (positionUrl) {
        positionUrl.addEventListener('input', debouncedSave);
    }

    if (contactPerson) {
        contactPerson.addEventListener('input', debouncedSave);
    }

    // Track job button click
    trackJobBtn.addEventListener('click', async () => {
        await trackJobApplication();
    });
}

async function trackJobApplication() {
    const companyNameInput = document.getElementById('company-name');
    const jobUrlInput = document.getElementById('position-url');
    const jobTitleInput = document.getElementById('position-title');
    const contactPersonInput = document.getElementById('contact-person');
    const contactPersonLinkedinInput = document.getElementById('contact-person-linkedin');
    const contactPersonEmailInput = document.getElementById('contact-person-email');
    const jobStateSelect = document.getElementById('job-state');
    const trackJobBtn = document.getElementById('track-job-btn');

    if (!companyNameInput || !jobUrlInput || !jobTitleInput || !jobStateSelect) {
        console.error('Required job tracking elements not found');
        return;
    }

    const companyName = companyNameInput.value.trim();
    const jobUrl = jobUrlInput.value.trim();
    const jobTitle = jobTitleInput.value.trim();
    const contactPerson = contactPersonInput ? contactPersonInput.value.trim() : '';
    const contactPersonLinkdein = contactPersonLinkedinInput ? contactPersonLinkedinInput.value.trim() : '';
    const contactPersonEmail = contactPersonEmailInput ? contactPersonEmailInput.value.trim() : '';
    const jobState = jobStateSelect.value;

    // Validation
    if (!companyName || !jobUrl) {
        showAlert('Please fill in Company Name and Position URL.', 'warning');
        if (!companyName) companyNameInput.focus();
        else jobUrlInput.focus();
        return;
    }

    if (!jobState) {
        showAlert('Please select a Job State.', 'warning');
        jobStateSelect.focus();
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

    try {
        const response = await window.pywebview.api.track_job_application(
            userId,
            companyName,
            jobUrl,
            jobTitle,
            jobState,
            contactPerson || null,
            contactPersonLinkdein || null,
            contactPersonEmail || null
        );

        if (response && response.code === 'OK') {
            showAlert('Job application tracked successfully!', 'success');
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