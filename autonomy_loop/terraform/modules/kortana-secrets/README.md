# Kor'tana Secrets Terraform Module

This module provisions and manages all necessary secrets for the Kor'tana application in AWS Secrets Manager, following best practices for security and maintainability.

It creates individual secrets for single values and uses JSON blobs only for tightly-coupled values that should be managed together.

## Features

-   Creates all required secrets with a consistent naming convention (`kortana/{env}/{SECRET_NAME}`).
-   Applies standardized tags for easy cost allocation and resource management.
-   Separates simple string secrets from complex JSON objects.
-   Allows secret values to be passed via variables, ideal for CI/CD pipelines.
-   Outputs the ARNs and IDs of all created secrets for easy reference in other parts of your infrastructure (e.g., IAM policies, ECS task definitions).

## Usage

Create a `secrets.tf` file (or similar) in your main Terraform configuration and instantiate the module:

```hcl
module "kortana_secrets" {
  source = "./modules/kortana-secrets"

  env = "prod" // or "dev"

  // Provide secret values via variables
  // In a CI/CD pipeline, these would be set via environment variables (TF_VAR_...)
  secrets_string = {
    "OPENAI_API_KEY"       = "sk-proj-..."
    "ANTHROPIC_API_KEY"    = "sk-ant-..."
    "GOOGLE_API_KEY"       = "AIzaSy..."
    "OPENROUTER_API_KEY"   = "sk-or-v1-..."
    "XAI_API_KEY"          = "gsk-..."
    "PINECONE_API_KEY"     = "..."
    "PINECONE_ENVIRONMENT" = "gcp-starter"
    "DISCORD_BOT_TOKEN"    = "..."
    "SESSION_SALT"         = "..."
  }

  stripe_keys = {
    secret_key      = "sk_test_..."
    publishable_key = "pk_test_..."
    webhook_secret  = "whsec_..."
  }

  // ... other JSON secret blocks
}
```

Then, you can reference the outputs in other resources, for example, an IAM policy:

```hcl
resource "aws_iam_policy" "discord_bot_policy" {
  name = "DiscordBotSecretsPolicy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = "secretsmanager:GetSecretValue"
        Effect   = "Allow"
        Resource = module.kortana_secrets.secret_arns["DISCORD_BOT_TOKEN"]
      },
    ]
  })
}
```

## Inputs

See `variables.tf` for all available input variables.

## Outputs

See `outputs.tf` for all module outputs.
