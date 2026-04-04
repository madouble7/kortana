# OpenAI Support Request Template

Use this as the message body for OpenAI support.

## Subject

Unauthorized API usage from compromised key; request for investigation and refund

## Message

Hello OpenAI Support,

I am reporting unauthorized API usage caused by a compromised OpenAI API key. I have already revoked the affected key.

Over the last two days, approximately `$66` in usage was incurred without my authorization. During review I found unexpected fine-tuning activity associated with my account or project, including:

- fine-tuning job: `ftjob-RvRsPoQh4THmdlkRrGev8QNB`
- fine-tuned model: `ft:gpt-4o-mini-2024-07-18:personal::DQr7bi2L`
- training file: `file-Uzcu85AixNAyedbvnLx3WV`
- additional job observed in dashboard history: `ftjob-HnZIxMYcQwdEACQPTQ6QjQ2G`

Known timing from the dashboard for the main unauthorized job:

- created: `2026-04-04 03:54 AM` America/Chicago
- started: `2026-04-04 03:55 AM`
- completed: `2026-04-04 04:10:28 AM`

I have preserved local evidence, including downloaded training artifacts and metrics from the OpenAI dashboard, and I can provide screenshots if needed.

Please help with the following:

1. investigate the unauthorized usage and confirm which project, key, or actor initiated it
2. review whether the charges can be refunded or credited due to compromise
3. confirm whether there were any other unauthorized actions on my account or projects
4. advise whether I should remove any additional project members, service accounts, or fine-tuned models beyond the revoked key

Actions I have already taken:

- revoked the compromised API key
- preserved evidence and timestamps
- reviewed unexpected fine-tune artifacts

If useful, I can provide:

- usage screenshots
- fine-tuning job screenshots
- local file hashes for downloaded artifacts
- browser timestamps showing dashboard inspection of the related resources

Thank you.

## Short Version

Hello, my OpenAI API key was compromised and used for unauthorized API activity resulting in about `$66` of unexpected charges over two days. I revoked the key already. I found unexpected fine-tuning activity including job `ftjob-RvRsPoQh4THmdlkRrGev8QNB` and model `ft:gpt-4o-mini-2024-07-18:personal::DQr7bi2L`. Please investigate the unauthorized usage, confirm the source, and let me know whether the charges can be refunded or credited.
