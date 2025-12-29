async function trackPositionsFromText(userId, text) {
    if (!userId || !text) {
        return { job: {}, company_name: "" };
    }

    const lines = text.trim().split('\n');
    const knownJobTitlesKeywords = await getJobTitleKeywords();
    
    let jobUrl = null;
    let contactLinkedin = null;
    let contactName = null;
    let jobState = "UNKNOWN";
    let contactEmail = null;
    let potentialCompanyNames = [];
    let jobTitle = "Unknown Position";

    for (const line of lines) {
        const trimmedLine = line.trim();
        if (!trimmedLine) continue;

        if (trimmedLine.includes("@")) {
            if (trimmedLine.split('@').length === 2 && trimmedLine.split('@')[1].includes('.')) {
                contactEmail = trimmedLine;
            }
            continue;
        }

        if (isUrl(trimmedLine)) {
            if (trimmedLine.toLowerCase().includes('linkedin.com')) {
                if (trimmedLine.includes('/in/')) {
                    [contactLinkedin, contactName] = getContactNameAndLinkedin(trimmedLine);
                } else {
                    jobUrl = trimmedLine;
                }
            } else {
                jobUrl = trimmedLine;
            }
            continue;
        }

        if (isJobState(trimmedLine)) {
            jobState = getJobState(trimmedLine);
            continue;
        }

        if (trimmedLine.includes(' ')) {
            if (knownJobTitlesKeywords.some(keyword => trimmedLine.toLowerCase().includes(keyword))) {
                jobTitle = trimmedLine;
            } else {
                const companyName = trimmedLine.replace(/[^a-zA-Z0-9 ]/g, '').trim() || contactName;
                if (companyName) potentialCompanyNames.push(companyName);
            }
        } else {
            potentialCompanyNames.push(trimmedLine);
        }
    }

    if (!jobUrl) {
        return { job: { error: "No job URL found" }, code: "ERROR" };
    }

    let companyName;
    if (!jobUrl.includes('linkedin.com')) {
        companyName = extractCompanyFromUrl(jobUrl);
    } else {
        companyName = extractCompanyName(potentialCompanyNames, contactName);
    }

    const trackedJob = {
        job_url: jobUrl,
        job_title: jobTitle,
        job_state: jobState,
        contact_name: contactName,
        contact_linkedin: contactLinkedin,
        contact_email: contactEmail
    };

    return {"job": trackedJob, "company_name": companyName}
}

function isUrl(text) {
    try {
        new URL(text);
        return true;
    } catch {
        return false;
    }
}

function isJobState(text) {
    const states = ['CONNECTION_REQUESTED', 'MESSAGE_SENT', 'EMAIL_SENT', 'APPLIED', 'UNKNOWN'];
    return states.includes(text.toUpperCase());
}

function getJobState(text) {
    const states = ['CONNECTION_REQUESTED', 'MESSAGE_SENT', 'EMAIL_SENT', 'APPLIED', 'UNKNOWN'];
    return states.includes(text.toUpperCase()) ? text.toUpperCase() : 'UNKNOWN';
}

async function getJobTitleKeywords() {
    try {
        const config = await window.pywebview.api.get_job_title_keywords();
        if (!config || Object.keys(config).length === 0) {
            return ["senior", "junior", "manager", "engineer", "analyst", "administrator", "designer", "writer"];
        }
        const titles = [];
        if (config.software_engineer) titles.push(...config.software_engineer);
        if (config.general) titles.push(...config.general);
        return titles;
    } catch {
        return ["senior", "junior", "manager", "engineer", "analyst", "administrator", "designer", "writer"];
    }
}

function getContactNameAndLinkedin(url) {
    const contactLinkedin = url;
    const contactName = getContactNameFromLinkedin(url);
    return [contactLinkedin, contactName];
}

function getContactNameFromLinkedin(url) {
    const match = url.match(/linkedin\.com\/in\/([^/?]+)/);
    if (!match) return null;
    
    const slug = match[1];
    return slug.split('-')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

function extractCompanyFromUrl(url) {
    try {
        const domain = new URL(url).hostname;
        return domain.replace('www.', '').split('.')[0];
    } catch {
        return "Unknown Company";
    }
}

function extractCompanyName(potentialCompanyNames, contactName) {
    for (const name of potentialCompanyNames) {
        if (name !== contactName) {
            return name;
        }
    }
    return "Unknown Company";
}