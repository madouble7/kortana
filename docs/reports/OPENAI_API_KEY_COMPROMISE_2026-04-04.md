# OpenAI API Key Compromise Incident

Date: 2026-04-04
Status: Open
Severity: High

## Summary

An OpenAI API key associated with this environment appears to have been compromised and used to create at least one unexpected fine-tuning job and incur approximately `$66` of unauthorized usage over a two-day period.

The key has since been revoked.

This report captures the local forensic evidence, the known OpenAI resource identifiers, and the immediate containment and recovery steps.

## Confirmed OpenAI Resources

- Fine-tuning job: `ftjob-RvRsPoQh4THmdlkRrGev8QNB`
- Fine-tuned model: `ft:gpt-4o-mini-2024-07-18:personal::DQr7bi2L`
- Training file: `file-Uzcu85AixNAyedbvnLx3WV`
- Additional fine-tuning job observed in browser history: `ftjob-HnZIxMYcQwdEACQPTQ6QjQ2G`

## Impact

- Unauthorized spend: approximately `$66`
- Unexpected fine-tuned model created in OpenAI account/project
- Unexpected training artifact persisted in account storage
- Potential exposure of broader account/project permissions depending on which key or project created the job

## Timeline

All times below are local machine observations or user-captured OpenAI dashboard times.

### OpenAI job timeline

- 2026-04-04 03:54 AM: fine-tuning job created
- 2026-04-04 03:55 AM: fine-tuning job started
- 2026-04-04 03:58 AM: checkpoints created and model evaluated against policy
- 2026-04-04 04:10:28 AM: job completed successfully

### Local machine observations

- 2026-04-04 12:43 PM to 12:46 PM: browser history shows dashboard inspection of:
  - fine-tuning job `ftjob-RvRsPoQh4THmdlkRrGev8QNB`
  - additional fine-tuning job `ftjob-HnZIxMYcQwdEACQPTQ6QjQ2G`
  - training file `file-Uzcu85AixNAyedbvnLx3WV`
  - related OpenAI storage and fine-tuning pages
- 2026-04-04 12:44:04 PM: local file [hp_style_dataset.jsonl](C:/Users/madou/Downloads/hp_style_dataset.jsonl) created in `Downloads`
- 2026-04-04 12:44:07 PM: local file [step_metrics.csv](C:/Users/madou/Downloads/step_metrics.csv) created in `Downloads`
- 2026-04-04 12:44:20 PM: Windows Recent shortcut for `hp_style_dataset.jsonl` created

## Local Forensic Evidence

### Training dataset

Path: [hp_style_dataset.jsonl](C:/Users/madou/Downloads/hp_style_dataset.jsonl)

- Size: `8,327` bytes
- Created: `2026-04-04 12:44:04 PM`
- SHA256: `5AE86627D48E1719E24A101AAA88B8A3C9410D26D7D0383ADA77DB9FDE57177C`
- Rows: `10`

Observed characteristics:

- The file is a small style-tuning dataset.
- Every example uses the same system instruction: write in the style of `J.K. Rowling`.
- Prompts are fantasy-writing prompts such as magical hallways, wizards, wand receipt, magical forest, and magical marketplace.
- This dataset is unrelated to Kor'tana's backend autonomy logic or operational identity.

### Download metadata

The file contains a Windows `Zone.Identifier` alternate data stream showing:

- `ReferrerUrl=https://platform.openai.com/`
- `HostUrl=https://fileserviceuploadsperm.blob.core.windows.net/files/file-Uzcu85AixNAyedbvnLx3WV...`

This strongly indicates the file was downloaded from the OpenAI dashboard later in the day, rather than authored locally at the time the fine-tune job started.

### Step metrics

Path: [step_metrics.csv](C:/Users/madou/Downloads/step_metrics.csv)

- Size: `904` bytes
- Created: `2026-04-04 12:44:07 PM`
- SHA256: `71A3EDDEFE9685C636AFB57DA701CD4549EAAC41E759A787335257927A66DD2D`

The file contents were base64-encoded CSV. After decoding:

- Steps: `30`
- First train loss: `3.03867`
- Best train loss: `0.78894` at step `26`
- Final train loss: `1.0845`
- First train accuracy: `0.44762`
- Best train accuracy: `0.83529` at step `22`
- Final train accuracy: `0.67544`
- Validation metrics: absent

Assessment:

- The run appears to be a small supervised style-tuning experiment.
- The final checkpoint is not the best step on the training curve.
- Because there is no validation set, the run is not suitable evidence of a robust or production-worthy model.

## What Was Searched Locally

The following local checks were performed:

- repository-wide search for fine-tuning API usage, job ids, file ids, and dataset names
- PowerShell history search
- scheduled task search
- VS Code workspace storage search
- Codex session search
- browser history search
- recent files and Windows shortcut metadata

## Findings

### Found

- Browser history confirming later manual inspection of the fine-tune job and file pages
- Downloaded training dataset and metrics files in `Downloads`
- Windows shortcut metadata confirming the training dataset file was opened locally

### Not found

- No checked-in script in this repo that creates OpenAI fine-tuning jobs
- No local script artifact containing the job id, file id, or training filename before later dashboard inspection
- No scheduled task or local execution log tying the 03:54 AM event to a script on this machine
- No Codex session directory for `2026-04-04` showing a local AI-agent launch path

## Credential State

At the time of investigation:

- local `.env` OpenAI API key returned `401 invalid_api_key`
- key has since been revoked by the user

This means the local repo key available during investigation could not query the job via the public API.

## Assessment

Current evidence does not support the claim that Kor'tana autonomously created her own model from this repository.

Current evidence supports a narrower conclusion:

- a fine-tuning job existed in the relevant OpenAI account or project
- the training artifacts were later downloaded manually from the OpenAI dashboard
- the job may have been launched from:
  - another valid API key
  - a different OpenAI project
  - the dashboard directly
  - another machine or script outside this repository

## Containment Actions Completed

- Revoked compromised OpenAI API key
- Preserved local training artifacts
- Preserved known resource identifiers and timestamps

## Recommended Immediate Actions

1. Contact OpenAI support and request investigation plus refund or credit for unauthorized usage.
2. Review all OpenAI projects, project members, service accounts, and API keys.
3. Remove unknown fine-tuned models and files after support has confirmed they are no longer needed for investigation.
4. Change account password and enable MFA if not already enabled.
5. Rotate any other exposed provider keys visible in local editor context.

## Recommended Follow-Up Hardening

1. Use project-scoped keys only.
2. Restrict keys to only required endpoints.
3. Separate experimental projects from production projects.
4. Add model allowlists so production cannot silently switch to unknown `ft:` models.
5. Add lower usage alerts and tighter project-level monitoring.

## Support Ticket Evidence Checklist

- Screenshot of unexpected usage and charges
- Screenshot of fine-tuning job `ftjob-RvRsPoQh4THmdlkRrGev8QNB`
- Screenshot of any related second job `ftjob-HnZIxMYcQwdEACQPTQ6QjQ2G`
- File ids and model ids listed above
- Local artifact hashes listed above
- Statement that compromised key has already been revoked
