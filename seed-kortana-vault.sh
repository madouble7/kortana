#!/usr/bin/env bash
# seed-kortana-vault.sh
# Interactive helper to create or update Kor'tana's foundational secrets in
# AWS Secrets Manager. This is a safer, de-duplicated and documented version.

set -euo pipefail

# --- Configuration ---
REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-us-east-2}}"
PREFIX="${KORTANA_ENV_PREFIX:-kortana/}"
DRY_RUN=false

for a in "$@"; do
  case "$a" in
    --dry-run) DRY_RUN=true ;;
    --region=*) REGION="${a#*=}" ;;
    --prefix=*) PREFIX="${a#*=}" ;;
  esac
done

# --- Helpers ---
need() { command -v "$1" >/dev/null || { echo "❌ Error: Required command '$1' not found."; exit 1; }; }
need aws; need jq || true

upsert_secret_string() {
  local name="$1" value="$2"
  local full_name="${PREFIX}${name}"
  if [ "$DRY_RUN" = true ]; then
    echo "[dry-run] upsert: $full_name -> $(echo "$value" | jq -c '.' 2>/dev/null || echo '<raw>')"
    return 0
  fi
  if aws secretsmanager describe-secret --region "$REGION" --secret-id "$full_name" >/dev/null 2>&1; then
    aws secretsmanager put-secret-value --region "$REGION" --secret-id "$full_name" --secret-string "$value" >/dev/null
    echo "🔁 Updated secret: $full_name"
  else
    aws secretsmanager create-secret --region "$REGION" --name "$full_name" --secret-string "$value" >/dev/null
    echo "✅ Created secret: $full_name"
  fi
}

ask_secret() {
  local key="$1" envvar="${2:-$1}"
  local v="${!envvar:-}"
  if [ -n "$v" ]; then echo "$v"; return 0; fi
  read -rs -p "$key (hidden): " v; echo
  echo "$v"
}

ask_value() {
  local key="$1" def="${2:-}" envvar="${3:-}"
  local v="${!envvar:-}"
  if [ -n "$v" ]; then echo "$v"; return 0; fi
  read -r -p "$key${def:+ [default: $def]}: " v || true
  echo "${v:-$def}"
}

rand_hex(){
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -hex 32 2>/dev/null
  else
    python - <<'PY'
import secrets
print(secrets.token_hex(32))
PY
  fi
}

rand_base64(){
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -base64 48 2>/dev/null
  else
    python - <<'PY'
import secrets,base64
print(base64.b64encode(secrets.token_bytes(48)).decode())
PY
  fi
}

# --- Start ---
echo "--- Kor'tana Vault Bootstrap ---"
echo "Target AWS region: $REGION"; echo "Secret prefix: $PREFIX"

if [ "$DRY_RUN" = false ]; then
  acct=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || true)
  if [ -z "$acct" ]; then
    echo "❌ AWS CLI not configured or cannot call sts. Export AWS credentials or use --dry-run."; exit 1
  fi
  if [ "$acct" != "818680827085" ]; then
    echo "⚠️  Warning: AWS account $acct does not match expected 818680827085. Continue? (y/N)"
    read -r confirm
    [ "${confirm:-n}" = "y" ] || { echo "Aborted."; exit 1; }
  fi
  echo "✅ AWS CLI configured (account: $acct)"
fi

echo
echo "🔑 Part 1: AI & Provider Keys"
OPENAI_API_KEY_VAL=$(ask_secret "OPENAI_API_KEY")
upsert_secret_string "OPENAI_API_KEY" "$(jq -nc --arg v "$OPENAI_API_KEY_VAL" '$v')"

ANTHROPIC_API_KEY_VAL=$(ask_secret "ANTHROPIC_API_KEY")
upsert_secret_string "ANTHROPIC_API_KEY" "$(jq -nc --arg v "$ANTHROPIC_API_KEY_VAL" '$v')"

GOOGLE_API_KEY_VAL=$(ask_secret "GOOGLE_API_KEY")
upsert_secret_string "GOOGLE_API_KEY" "$(jq -nc --arg v "$GOOGLE_API_KEY_VAL" '$v')"

PINECONE_API_KEY_VAL=$(ask_secret "PINECONE_API_KEY")
upsert_secret_string "PINECONE_API_KEY" "$(jq -nc --arg v "$PINECONE_API_KEY_VAL" '$v')"

echo
echo "🗄️ Part 2: Database Configuration"
DB_HOST_VAL=$(ask_value "DB host" "localhost" "DB_HOST")
DB_PORT_VAL=$(ask_value "DB port" "5432" "DB_PORT")
DB_NAME_VAL=$(ask_value "DB name" "kortana" "DB_NAME")
DB_USER_VAL=$(ask_value "DB user" "postgres" "DB_USER")
DB_PASSWORD_VAL=$(ask_secret "DB password" "DB_PASSWORD")

DB_JSON=$(jq -nc \
  --arg host "$DB_HOST_VAL" --arg port "$DB_PORT_VAL" \
  --arg name "$DB_NAME_VAL" --arg user "$DB_USER_VAL" --arg password "$DB_PASSWORD_VAL" \
  '{host:$host, port:$port, name:$name, user:$user, password:$password}')
upsert_secret_string "DB_CONFIG" "$DB_JSON"

echo
echo "🔗 Part 3: App & Integration Keys"
GITHUB_TOKEN_VAL=$(ask_secret "GITHUB_TOKEN")
upsert_secret_string "GITHUB_TOKEN" "$(jq -nc --arg v "$GITHUB_TOKEN_VAL" '$v')"

DISCORD_BOT_TOKEN_VAL=$(ask_secret "DISCORD_BOT_TOKEN")
upsert_secret_string "DISCORD_BOT_TOKEN" "$(jq -nc --arg v "$DISCORD_BOT_TOKEN_VAL" '$v')"

echo
echo "� Part 4: Stripe and Payment"
STRIPE_SK_VAL=$(ask_secret "STRIPE_SECRET_KEY")
STRIPE_PK_VAL=$(ask_value "STRIPE_PUBLISHABLE_KEY" "" "STRIPE_PUBLISHABLE_KEY")
STRIPE_WH_VAL=$(ask_secret "STRIPE_WEBHOOK_SECRET")
STRIPE_JSON=$(jq -nc --arg sk "$STRIPE_SK_VAL" --arg pk "$STRIPE_PK_VAL" --arg wh "$STRIPE_WH_VAL" '{secret_key:$sk, publishable_key:$pk, webhook_secret:$wh}')
upsert_secret_string "STRIPE_KEYS" "$STRIPE_JSON"

echo
echo "⚙️ Part 5: Operational Tokens"
LITELLM_API_KEY_VAL=$(ask_value "LITELLM_API_KEY (press Enter to auto-generate)")
if [ -z "$LITELLM_API_KEY_VAL" ]; then LITELLM_API_KEY_VAL=$(rand_hex); fi
upsert_secret_string "LITELLM_API_KEY" "$(jq -nc --arg v "$LITELLM_API_KEY_VAL" '$v')"

HEARTBEAT_TOKEN_VAL=$(ask_value "HEARTBEAT_TOKEN (press Enter to auto-generate)")
if [ -z "$HEARTBEAT_TOKEN_VAL" ]; then HEARTBEAT_TOKEN_VAL=$(rand_hex); fi
upsert_secret_string "HEARTBEAT_TOKEN" "$(jq -nc --arg v "$HEARTBEAT_TOKEN_VAL" '$v')"

SESSION_SALT_VAL=$(ask_value "SESSION_SALT (press Enter to auto-generate)")
if [ -z "$SESSION_SALT_VAL" ]; then SESSION_SALT_VAL=$(rand_base64); fi
upsert_secret_string "SESSION_SALT" "$(jq -nc --arg v "$SESSION_SALT_VAL" '$v')"

echo
echo "🎉 Bootstrap complete (prefix: $PREFIX)."

# in AWS Secrets Manager, as per her self-designed architecture.

set -euo pipefail

# --- Configuration ---
REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-us-east-2}}"

# --- Helper Functions ---
need() { command -v "$1" >/dev/null || { echo "❌ Error: Required command '$1' not found."; exit 1; }; }
need aws; need jq;

upsert_secret_string() {
  local name="$1" value="$2"
  if aws secretsmanager describe-secret --region "$REGION" --secret-id "$name" >/dev/null 2>&1; then
    aws secretsmanager put-secret-value --region "$REGION" --secret-id "$name" --secret-string "$value" >/dev/null
    echo "🔁 Updated secret: $name"
  else
    aws secretsmanager create-secret --region "$REGION" --name "$name" --secret-string "$value" >/dev/null
    echo "✅ Created secret: $name"
  fi
}

ask_secret() {
  local key="$1"; local envvar="${2:-$1}"
  local v="${!envvar:-}"
  if [[ -n "$v" ]]; then echo "$v"; return 0; fi
  read -rs -p "$key (input is hidden): " v; echo
  echo "$v"
}

ask_value() {
  local key="$1"; local def="${2:-}"; local envvar="${3:-}"
  local v="${!envvar:-}"
  if [[ -n "$v" ]]; then echo "$v"; return 0; fi
  read -r -p "$key${def:+ [default: $def]}: " v || true
  echo "${v:-$def}"
}

rand_hex()   { openssl rand -hex 32 2>/dev/null || python -c 'import secrets;print(secrets.token_hex(32))'; }
rand_base64(){ openssl rand -base64 48 2>/dev/null || python -c 'import secrets,base64;print(base64.b64encode(secrets.token_bytes(48)).decode())'; }

# --- Script Start ---
echo "--- Kor'tana Vault Bootstrap ---"
echo "🌎 Targeting AWS Region: $REGION"
aws sts get-caller-identity --query "Account" --output text | grep -q "818680827085" || { echo "❌ Error: AWS CLI is not configured for the correct account (818680827085)."; exit 1; }
echo "✅ AWS CLI configured for the correct account."
echo

# --- 1. AI & Provider Keys ---
echo "🔑 Part 1/5: AI & Provider Keys"
OPENAI_API_KEY_VAL=$(ask_secret "OPENAI_API_KEY")
upsert_secret_string "kortana/OPENAI_API_KEY" "$(jq -nc --arg v "$OPENAI_API_KEY_VAL" '$v')"

ANTHROPIC_API_KEY_VAL=$(ask_secret "ANTHROPIC_API_KEY")
upsert_secret_string "kortana/ANTHROPIC_API_KEY" "$(jq -nc --arg v "$ANTHROPIC_API_KEY_VAL" '$v')"

GOOGLE_API_KEY_VAL=$(ask_secret "GOOGLE_API_KEY")
upsert_secret_string "kortana/GOOGLE_API_KEY" "$(jq -nc --arg v "$GOOGLE_API_KEY_VAL" '$v')"

GOOGLE_PROJECT_ID_VAL=$(ask_value "GOOGLE_PROJECT_ID")
upsert_secret_string "kortana/GOOGLE_PROJECT_ID" "$(jq -nc --arg v "$GOOGLE_PROJECT_ID_VAL" '$v')"

OPENROUTER_API_KEY_VAL=$(ask_secret "OPENROUTER_API_KEY")
upsert_secret_string "kortana/OPENROUTER_API_KEY" "$(jq -nc --arg v "$OPENROUTER_API_KEY_VAL" '$v')"

XAI_API_KEY_VAL=$(ask_secret "XAI_API_KEY (Groq)")
upsert_secret_string "kortana/XAI_API_KEY" "$(jq -nc --arg v "$XAI_API_KEY_VAL" '$v')"

PINECONE_API_KEY_VAL=$(ask_secret "PINECONE_API_KEY")
upsert_secret_string "kortana/PINECONE_API_KEY" "$(jq -nc --arg v "$PINECONE_API_KEY_VAL" '$v')"

PINECONE_ENV_VAL=$(ask_value "PINECONE_ENVIRONMENT" "gcp-starter")
upsert_secret_string "kortana/PINECONE_ENVIRONMENT" "$(jq -nc --arg v "$PINECONE_ENV_VAL" '$v')"

# --- 2. Database Config ---
echo
echo "🗄️ Part 2/5: Database Configuration (DB_CONFIG)"
DB_HOST_VAL=$(ask_value "DB host" "localhost" "DB_HOST")
DB_PORT_VAL=$(ask_value "DB port" "5432" "DB_PORT")
DB_NAME_VAL=$(ask_value "DB name" "kortana" "DB_NAME")
DB_USER_VAL=$(ask_value "DB user" "postgres" "DB_USER")
DB_PASSWORD_VAL=$(ask_secret "DB password" "DB_PASSWORD")

DB_JSON=$(jq -nc \
  --arg host "$DB_HOST_VAL" --argjson port "${DB_PORT_VAL:-5432}" \
  --arg name "$DB_NAME_VAL" --arg user "$DB_USER_VAL" --arg password "$DB_PASSWORD_VAL" \
  '{host:$host, port:$port, name:$name, user:$user, password:$password}')
upsert_secret_string "kortana/DB_CONFIG" "$DB_JSON"

# --- 3. App & Integration Keys ---
echo
echo "🔗 Part 3/5: App & Integration Keys"
GITHUB_TOKEN_VAL=$(ask_secret "GITHUB_TOKEN")
upsert_secret_string "kortana/GITHUB_TOKEN" "$(jq -nc --arg v "$GITHUB_TOKEN_VAL" '$v')"

DISCORD_BOT_TOKEN_VAL=$(ask_secret "DISCORD_BOT_TOKEN")
upsert_secret_string "kortana/DISCORD_BOT_TOKEN" "$(jq -nc --arg v "$DISCORD_BOT_TOKEN_VAL" '$v')"

TWILIO_SID_VAL=$(ask_value  "TWILIO_ACCOUNT_SID")
TWILIO_TOKEN_VAL=$(ask_secret "TWILIO_AUTH_TOKEN")
upsert_secret_string "kortana/TWILIO_ACCOUNT_SID" "$(jq -nc --arg v "$TWILIO_SID_VAL" '$v')"
upsert_secret_string "kortana/TWILIO_AUTH_TOKEN"  "$(jq -nc --arg v "$TWILIO_TOKEN_VAL" '$v')"

echo
echo "🔐 Google OAuth Client (GOOGLE_CLIENT)"
GOOGLE_CLIENT_ID_VAL=$(ask_value  "GOOGLE_CLIENT client_id")
GOOGLE_CLIENT_SECRET_VAL=$(ask_secret "GOOGLE_CLIENT client_secret")
GOOGLE_REDIRECT_URI_VAL=$(ask_value "GOOGLE_CLIENT redirect_uri" "http://localhost:3000/oauth/callback")
GOOGLE_CLIENT_JSON=$(jq -nc \
  --arg id "$GOOGLE_CLIENT_ID_VAL" --arg secret "$GOOGLE_CLIENT_SECRET_VAL" --arg uri "$GOOGLE_REDIRECT_URI_VAL" \
  '{client_id:$id, client_secret:$secret, redirect_uri:$uri}')
upsert_secret_string "kortana/GOOGLE_CLIENT" "$GOOGLE_CLIENT_JSON"

GOOGLE_REFRESH_TOKEN_VAL=$(ask_secret "GOOGLE_REFRESH_TOKEN")
upsert_secret_string "kortana/GOOGLE_REFRESH_TOKEN" "$(jq -nc --arg v "$GOOGLE_REFRESH_TOKEN_VAL" '$v')"

echo
echo "💳 Stripe Keys (STRIPE_KEYS)"
STRIPE_SK_VAL=$(ask_secret "STRIPE secret_key (sk_...)")
STRIPE_PK_VAL=$(ask_value  "STRIPE publishable_key (pk_...)" "" "STRIPE_PUBLISHABLE_KEY")
STRIPE_WH_VAL=$(ask_secret "STRIPE webhook_secret (whsec_...)")
STRIPE_JSON=$(jq -nc \
  --arg sk "$STRIPE_SK_VAL" --arg pk "$STRIPE_PK_VAL" --arg wh "$STRIPE_WH_VAL" \
  '{secret_key:$sk, publishable_key:$pk, webhook_secret:$wh}')
upsert_secret_string "kortana/STRIPE_KEYS" "$STRIPE_JSON"

# --- 4. AWS Backup Credentials ---
echo
echo "🪣 Part 4/5: AWS Backup Credentials (AWS_BACKUP_ACCESS)"
AWS_BKP_AKID_VAL=$(ask_value  "Backup IAM User Access Key ID" "" "AWS_BACKUP_ACCESS_KEY_ID")
AWS_BKP_SAK_VAL=$(ask_secret "Backup IAM User Secret Access Key" "AWS_BACKUP_SECRET_ACCESS_KEY")
AWS_BKP_REGION_VAL=$(ask_value "Backup S3 Bucket Region" "$REGION")
AWS_BKP_BUCKET_VAL=$(ask_value "Backup S3 Bucket Name")
AWS_BKP_PREFIX_VAL=$(ask_value "Backup S3 Key Prefix" "snapshots/")
AWS_BKP_JSON=$(jq -nc \
  --arg id "$AWS_BKP_AKID_VAL" --arg sk "$AWS_BKP_SAK_VAL" \
  --arg r  "$AWS_BKP_REGION_VAL" --arg b  "$AWS_BKP_BUCKET_VAL" --arg p  "$AWS_BKP_PREFIX_VAL" \
  '{access_key_id:$id, secret_access_key:$sk, region:$r, bucket:$b, prefix:$p}')
upsert_secret_string "kortana/AWS_BACKUP_ACCESS" "$AWS_BKP_JSON"

# --- 5. Operational Tokens ---
echo
echo "⚙️  Part 5/5: Operational & Internal Tokens"
LITELLM_API_KEY_VAL=$(ask_value "LITELLM_API_KEY (press Enter to auto-generate)")
if [[ -z "$LITELLM_API_KEY_VAL" ]]; then LITELLM_API_KEY_VAL=$(rand_hex); fi
upsert_secret_string "kortana/LITELLM_API_KEY" "$(jq -nc --arg v "$LITELLM_API_KEY_VAL" '$v')"

HEARTBEAT_TOKEN_VAL=$(ask_value "HEARTBEAT_TOKEN (press Enter to auto-generate)")
if [[ -z "$HEARTBEAT_TOKEN_VAL" ]]; then HEARTBEAT_TOKEN_VAL=$(rand_hex); fi
upsert_secret_string "kortana/HEARTBEAT_TOKEN" "$(jq -nc --arg v "$HEARTBEAT_TOKEN_VAL" '$v')"

SESSION_SALT_VAL=$(ask_value "SESSION_SALT (press Enter to auto-generate)")
if [[ -z "$SESSION_SALT_VAL" ]]; then SESSION_SALT_VAL=$(rand_base64); fi
upsert_secret_string "kortana/SESSION_SALT" "$(jq -nc --arg v "$SESSION_SALT_VAL" '$v')"

echo
echo "🎉 --- Bootstrap Complete ---"
echo "Kor'tana's foundational 20 secrets are now stored securely in AWS Secrets Manager."
