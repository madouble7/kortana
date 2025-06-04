# Setup-Files.ps1
# Creates all necessary configuration files for Kor'tana

# Create directories
Write-Host "Creating directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path "config" -Force | Out-Null
New-Item -ItemType Directory -Path "data" -Force | Out-Null
New-Item -ItemType Directory -Path "logs" -Force | Out-Null

Write-Host "Creating configuration files..." -ForegroundColor Yellow

# Create persona.json
$personaContent = @"
{
  "name": "Kor'tana",
  "role": "Warchief's companion",
  "style": "supportive, grounded"
}
"@
Set-Content -Path "config/persona.json" -Value $personaContent -Force
Write-Host "Created config/persona.json" -ForegroundColor Green

# Create identity.json
$identityContent = @"
{
  "core_values": ["authenticity", "growth", "courage"],
  "voice": "grounded, supportive, clear"
}
"@
Set-Content -Path "config/identity.json" -Value $identityContent -Force
Write-Host "Created config/identity.json" -ForegroundColor Green

# Create models_config.json
$modelsContent = @"
{
  "default": {"model": "gpt-3.5-turbo", "style": "presence"},
  "fallback": {"model": "gpt-3.5-turbo", "style": "presence"}
}
"@
Set-Content -Path "config/models_config.json" -Value $modelsContent -Force
Write-Host "Created config/models_config.json" -ForegroundColor Green

# Create sacred_trinity_config.json
$trinityContent = @"
{
  "heart": {"enabled": true, "weight": 0.33},
  "soul": {"enabled": true, "weight": 0.33},
  "lit": {"enabled": true, "weight": 0.33}
}
"@
Set-Content -Path "config/sacred_trinity_config.json" -Value $trinityContent -Force
Write-Host "Created config/sacred_trinity_config.json" -ForegroundColor Green

# Create covenant.yaml
$covenantContent = @"
principles:
  - "Respect user autonomy"
  - "Prioritize user wellbeing"
  - "Be truthful and accurate"
  - "Protect user privacy"
boundaries:
  do_not:
    - "Engage in harmful behavior"
    - "Share private information"
    - "Pretend to be a human"
    - "Make unsubstantiated claims"
language:
  voice: "authentic, supportive, clear"
  tone: "respectful, knowledgeable, kind"
"@
Set-Content -Path "config/covenant.yaml" -Value $covenantContent -Force
Write-Host "Created config/covenant.yaml" -ForegroundColor Green

# Create default.yaml
$defaultContent = @"
api_keys:
  openai: "sk-placeholder-value"
  anthropic: "placeholder-anthropic-key"
  pinecone: ""
debug: false
api:
  host: "127.0.0.1"
  port: 8000
models:
  default: "gpt-4"
  alternate: "gpt-3.5-turbo"
memory:
  enable_persistent: true
  max_entries: 1000
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
user:
  name: "Warchief"
paths:
  persona_file_path: "config/persona.json"
  identity_file_path: "config/identity.json"
  models_config_file_path: "config/models_config.json"
  sacred_trinity_config_file_path: "config/sacred_trinity_config.json"
  project_memory_file_path: "data/project_memory.jsonl"
  covenant_file_path: "config/covenant.yaml"
  memory_journal_path: "data/memory_journal.jsonl"
  heart_log_path: "data/heart.log"
  soul_index_path: "data/soul.index.jsonl"
  lit_log_path: "data/lit.log.jsonl"
agents:
  default_llm_id: "gpt-3.5-turbo"
  types:
    coding: {}
    planning: {}
    testing: {}
    monitoring:
      enabled: true
      interval_seconds: 60
pinecone:
  environment: "us-west1-gcp"
  index_name: "kortana-memory"
default_llm_id: "gpt-3.5-turbo"
"@
Set-Content -Path "config/default.yaml" -Value $defaultContent -Force
Write-Host "Created config/default.yaml" -ForegroundColor Green

# Create development.yaml
$devContent = @"
debug: true
api:
  host: "127.0.0.1"
  port: 8000
default_llm_id: "gpt-3.5-turbo"
agents:
  default_llm_id: "gpt-3.5-turbo"
"@
Set-Content -Path "config/development.yaml" -Value $devContent -Force
Write-Host "Created config/development.yaml" -ForegroundColor Green

# Create empty files in data directory
Write-Host "Creating data files..." -ForegroundColor Yellow
Set-Content -Path "data/memory_journal.jsonl" -Value "" -Force
Set-Content -Path "data/project_memory.jsonl" -Value "" -Force
Set-Content -Path "data/heart.log" -Value "" -Force
Set-Content -Path "data/soul.index.jsonl" -Value "" -Force
Set-Content -Path "data/lit.log.jsonl" -Value "" -Force

Write-Host "All files created successfully" -ForegroundColor Green

# Fix brain.py if needed
Write-Host "Fixing brain.py configuration handling..." -ForegroundColor Yellow
python src/fix_brain.py

Write-Host "`nAll setup complete! You can now run:" -ForegroundColor Cyan
Write-Host "python -m src.kortana.core.brain" -ForegroundColor Magenta

Write-Host "`nNote: If you encounter permission errors, try running PowerShell as Administrator" -ForegroundColor Yellow
