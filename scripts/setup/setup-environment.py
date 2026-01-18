#!/usr/bin/env python3
"""
Environment Setup Script for Kor'tana Autonomous System
Helps configure environment variables for local development, GitHub Actions, and Cloud Run

SECURITY NOTICE: Never commit real API keys to this file!
Use environment variables or secret managers instead.
"""

import os
import sys
from pathlib import Path

def setup_local_env():
    """Set up local development environment"""
    print("🏠 Setting up LOCAL DEVELOPMENT environment")
    print("=" * 50)
    print("⚠️  SECURITY: This will create a .env file with your API keys")
    print("   Never commit .env files to version control!")
    print()

    env_file = Path("backend/.env")

    if env_file.exists():
        print(f"⚠️  {env_file} already exists!")
        overwrite = input("Overwrite existing .env file? (y/N): ").lower().strip()
        if overwrite != 'y':
            print("Skipping local environment setup...")
            return

    # Copy from template
    template_file = Path("backend/.env.example")
    if not template_file.exists():
        print("❌ backend/.env.example not found!")
        return

    print("📋 Creating backend/.env from template...")

    # Read template
    with open(template_file, 'r') as f:
        content = f.read()

    # Prompt for required values
    print("\n🔑 Please provide your API keys:")
    print("(Get these from the respective service dashboards)")
    print()

    gemini_key = input("GEMINI_API_KEY (from Google AI Studio): ").strip()
    if not gemini_key:
        print("⚠️  No GEMINI_API_KEY provided - AI features won't work")
        gemini_key = "your-gemini-api-key-here"

    drive_key = input("GOOGLE_DRIVE_API_KEY (optional): ").strip()
    if not drive_key:
        drive_key = "your-google-drive-api-key-here"

    gcp_project = input("GOOGLE_PROJECT_ID (optional, for Cloud Run): ").strip()
    if not gcp_project:
        gcp_project = "your-gcp-project-id"

    # Update content
    content = content.replace("your-gemini-api-key-here", gemini_key)
    content = content.replace("your-google-drive-api-key-here", drive_key)
    content = content.replace("your-gcp-project-id", gcp_project)

    # Write .env file
    with open(env_file, 'w') as f:
        f.write(content)

    print(f"✅ Created {env_file}")
    print("🔒 IMPORTANT: Add .env to .gitignore and never commit it!")

def setup_github_secrets():
    """Guide for setting up GitHub Actions secrets"""
    print("🔐 Setting up GITHUB ACTIONS secrets")
    print("=" * 50)
    print("📍 Location: Repository → Settings → Secrets and variables → Actions")
    print()

    secrets = {
        "KORTANA_AUTONOMOUS_TOKEN": {
            "description": "GitHub PAT for autonomous operations (repo, workflow scopes)",
            "source": "GitHub: Settings → Developer settings → Personal access tokens",
            "required": True
        },
        "GEMINI_API_KEY": {
            "description": "Google Gemini API key for AI analysis",
            "source": "Google AI Studio: https://aistudio.google.com/app/apikey",
            "required": True
        },
        "GITHUB_TOKEN": {
            "description": "GitHub token for API access (automatically provided)",
            "source": "Automatically provided by GitHub Actions",
            "required": False
        },
        "GCP_WORKLOAD_IDENTITY_PROVIDER": {
            "description": "GCP Workload Identity Provider for OIDC auth",
            "source": "GCP Console → IAM → Workload Identity Federation",
            "required": False
        },
        "GCP_SERVICE_ACCOUNT": {
            "description": "GCP Service Account email for Cloud Run",
            "source": "GCP Console → IAM → Service Accounts",
            "required": False
        }
    }

    print("📋 Required GitHub Repository Secrets:")
    print()

    for secret_name, info in secrets.items():
        req_marker = "🔴" if info["required"] else "🟡"
        print(f"{req_marker} **{secret_name}**")
        print(f"   {info['description']}")
        print(f"   Source: {info['source']}")
        print()

def setup_cloud_run_secrets():
    """Guide for setting up Cloud Run secrets"""
    print("☁️  Setting up CLOUD RUN secrets")
    print("=" * 50)
    print("📍 Location: GCP Console → Security → Secret Manager")
    print()

    secrets = [
        ("GEMINI_API_KEY", "Google Gemini API key"),
        ("GITHUB_TOKEN", "GitHub API token for repository access")
    ]

    for secret_name, description in secrets:
        print(f"🔐 **{secret_name}**")
        print(f"   {description}")
        print("   Commands:")
        print(f"   echo -n 'your-{secret_name.lower()}' | gcloud secrets create {secret_name} --data-file=-")
        print(f"   gcloud secrets add-iam-policy-binding {secret_name} \\")
        print("     --member='serviceAccount:YOUR_SERVICE_ACCOUNT' \\")
        print("     --role='roles/secretmanager.secretAccessor'")
        print()

def validate_environment():
    """Validate current environment setup"""
    print("🔍 Validating environment setup")
    print("=" * 50)

    checks = []

    # Check local .env
    env_file = Path("backend/.env")
    if env_file.exists():
        checks.append(("✅ Local .env file", "Found"))
    else:
        checks.append(("❌ Local .env file", "Missing - run local setup"))

    # Check if we're in GitHub Actions
    if os.getenv('GITHUB_ACTIONS'):
        checks.append(("✅ GitHub Actions", "Running in CI"))

        # Check for required secrets
        required_secrets = ['KORTANA_AUTONOMOUS_TOKEN', 'GEMINI_API_KEY']
        for secret in required_secrets:
            if os.getenv(secret):
                checks.append((f"✅ {secret}", "Set"))
            else:
                checks.append((f"❌ {secret}", "Missing"))
    else:
        checks.append(("ℹ️  Environment", "Local development"))

    # Print results
    for check, status in checks:
        print(f"{check}: {status}")

    return all("✅" in check for check, _ in checks)

def main():
    """Main setup function"""
    print("🚀 Kor'tana Environment Setup")
    print("🔒 SECURITY: This script helps you set up environment variables securely")
    print("   Never commit real API keys to files!")
    print()

    print("Choose your setup scenario:")
    print()
    print("1. 🏠 Local Development (.env file)")
    print("2. 🔐 GitHub Actions (repository secrets)")
    print("3. ☁️  Cloud Run (GCP secrets)")
    print("4. 🔍 Validate current setup")
    print("5. 💡 Show all options")
    print()

    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        choice = input("Enter your choice (1-5): ").strip()

    if choice == '1':
        setup_local_env()
    elif choice == '2':
        setup_github_secrets()
    elif choice == '3':
        setup_cloud_run_secrets()
    elif choice == '4':
        validate_environment()
    elif choice == '5':
        print("All setup options:")
        print()
        print("🏠 LOCAL DEVELOPMENT:")
        print("   Creates backend/.env file with your API keys")
        print("   Never commit .env files to git!")
        print()
        setup_github_secrets()
        print()
        setup_cloud_run_secrets()
    else:
        print("❌ Invalid choice. Run without arguments for menu.")
        sys.exit(1)

if __name__ == "__main__":
    main()
