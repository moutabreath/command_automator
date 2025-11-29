async function initJobTracking() {
    console.log('Initializing Job Tracking...');
    await initJobTrackingEventListeners();

}


function getStateLabel(enumName) {
    const stateLabels = {
        'CONNECTION_REQUESTED': 'Request Sent',
        'MESSAGE_SENT': 'Message Received',
        'EMAIL_SENT': 'Email Sent',
        'APPLIED': 'Applied',
        'UKNOWN': 'Unknown'
    };
    return stateLabels[enumName] || enumName;
}

async function loadJobApplicationStates() {
    try {
        const states = await window.pywebview.api.get_job_application_states();
        const stateSelect = document.getElementById('job-state');
        stateSelect.innerHTML = '';

        if (states && Array.isArray(states)) {
            states.forEach(state => {
                const option = document.createElement('option');
                option.value = state;
                option.textContent = getStateLabel(state);
                stateSelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading job application states:', error);
    }
}

async function loadJobTrackingConfig() {
    try {
        config = await window.pywebview.api.load_job_tracking_configuration();
        if (config === "" || config === " ") {
            return;
        }
        document.getElementById('company-name').value = config.company_name || '';
        document.getElementById('position-title').value = config.position_title || '';
        document.getElementById('position-url').value = config.position_url || '';
        document.getElementById('contact-person').value = config.contact_person || '';
    } catch (error) {
        console.log('Error loading config:', error);
        config = { selected_script: '', additional_text: '', flags: '' };
    }
}

async function saveJobTrackingConfig() {
    try {
        let jobTrackingConfig = {};
        jobTrackingConfig.company_name = document.getElementById('company-name').value;
        jobTrackingConfig.position_title = document.getElementById('position-title').value;
        jobTrackingConfig.position_url = document.getElementById('position-url').value;
        jobTrackingConfig.contact_person = document.getElementById('contact-person').value;

        const result = await window.pywebview.api.save_job_tracking_configuration(jobTrackingConfig);
    } catch (error) {
        console.log('Error saving config:', error);
    }
}

async function initJobTrackingEventListeners() {
    document.getElementById('company-name').addEventListener('input', async () => {
        await saveJobTrackingConfig();
    });
    document.getElementById('position-title').addEventListener('input', async () => {
        await saveJobTrackingConfig();
    });

    document.getElementById('position-url').addEventListener('input', async () => {
        await saveJobTrackingConfig();
    });
    document.getElementById('contact-person').addEventListener('input', async () => {
        await saveJobTrackingConfig();
    });

    document.getElementById('track-job-btn').addEventListener('click', async () => {
        await trackJobApplication();
    });
}

async function trackJobApplication() {
    const companyName = document.getElementById('company-name').value.trim();
    const jobUrl = document.getElementById('position-url').value.trim();
    const jobTitle = document.getElementById('position-title').value.trim();
    const contactPerson = document.getElementById('contact-person').value.trim();
    const jobState = document.getElementById('job-state').value;

    if (!companyName || !jobUrl) {
        alert('Please fill in Company Name and Position URL.');
        return;
    }

    if (!jobState) {
        alert('Please select a Job State.');
        return;
    }

    if (!user_id) {
        alert('Please login first.');
        return;
    }

    try {
        const response = await window.pywebview.api.track_job_application(
            user_id,
            companyName,
            jobUrl,
            jobTitle,
            jobState,
            contactPerson || null
        );
        alert('Job application tracked successfully!');
        // Clear inputs
        document.getElementById('company-name').value = '';
        document.getElementById('position-url').value = '';
        document.getElementById('contact-person').value = '';
        document.getElementById('contact-person').value = '';
    } catch (error) {
        console.error('Track job failed:', error);
        alert('Failed to track job. Please check the console for details.');
    }
}