import { trackPositionsFromText } from '../path/to/trackPositionsFromText';

// Mock data
const jobLink = "https://www.linkedin.com/jobs/view/4324949336";
const jobState = "applied";
const companyName = "finonex";
const jobTitle = "senior backend software engineer";
const contactName = "amirdar";
const contactLinkedin = "https://www.linkedin.com/in/amirdar/";
const contactName2 = "tal druckmann";
const contactLinkedin2 = "https://www.linkedin.com/in/tal-druckmann-88489520/";

describe('Job Tracking Text Parser Tests', () => {
    const userId = "test-user-123";

    test('should parse text with contact linkedin format', async () => {
        const text = `${jobLink}
${companyName}
${contactLinkedin2}
${jobState}
${jobTitle}
${contactName2}`;

        const result = await trackPositionsFromText(userId, text);

        expect(result).toBeTruthy();
        expect(result.code).toBe('OK');
        expect(result.job).toBeTruthy();
        expect(result.company_name).toBe(companyName);
        expect(result.job.job_url).toBe(jobLink);
        expect(result.job.job_state).toBe('APPLIED');
        expect(result.job.job_title).toBe(jobTitle);
        expect(result.job.contact_name).toBe(contactName2);
        expect(result.job.contact_linkedin).toBe(contactLinkedin2);
    });

    test('should parse text without email', async () => {
        const text = `${jobLink}
${companyName}
${contactLinkedin}
${jobState}
${jobTitle}
${contactName}`;

        const result = await trackPositionsFromText(userId, text);

        expect(result).toBeTruthy();
        expect(result.code).toBe('OK');
        expect(result.job).toBeTruthy();
        expect(result.company_name).toBe(companyName);
        expect(result.job.job_url).toBe(jobLink);
        expect(result.job.job_state).toBe('APPLIED');
        expect(result.job.job_title).toBe(jobTitle);
        expect(result.job.contact_name).toBe(contactName);
        expect(result.job.contact_linkedin).toBe(contactLinkedin);
    });

    test('should parse text without title', async () => {
        const text = `${jobLink}
${companyName}
${contactLinkedin}
${jobState}
${contactName}`;

        const result = await trackPositionsFromText(userId, text);

        expect(result).toBeTruthy();
        expect(result.code).toBe('OK');
        expect(result.job).toBeTruthy();
        expect(result.company_name).toBe(companyName);
        expect(result.job.job_url).toBe(jobLink);
        expect(result.job.job_state).toBe('APPLIED');
        expect(result.job.job_title).toBe('Unknown Position');
        expect(result.job.contact_name).toBe(contactName);
        expect(result.job.contact_linkedin).toBe(contactLinkedin);
    });

    test('should parse text without status', async () => {
        const text = `${jobLink}
${companyName}
${contactLinkedin}
${jobTitle}
${contactName}`;

        const result = await trackPositionsFromText(userId, text);

        expect(result).toBeTruthy();
        expect(result.code).toBe('OK');
        expect(result.job).toBeTruthy();
        expect(result.company_name).toBe(companyName);
        expect(result.job.job_url).toBe(jobLink);
        expect(result.job.job_state).toBe('UNKNOWN');
        expect(result.job.job_title).toBe(jobTitle);
        expect(result.job.contact_name).toBe(contactName);
        expect(result.job.contact_linkedin).toBe(contactLinkedin);
    });
});