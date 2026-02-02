# OpenClaw Lite

Lightweight API-only LLM router. Routes queries between OpenAI (cheap/fast) and Claude (powerful) based on complexity.

## Features

- **No GPU required** - Pure API-based, runs on cheap VPS (~$10-15/month)
- **Intelligent routing** - Simple queries → OpenAI GPT-4o-mini, Complex queries → Claude Sonnet 4
- **Cost tracking** - Per-provider usage tracking with monthly budgets
- **Security hardened** - UFW firewall, Fail2ban, SSL/TLS, rate limiting
- **One-command deploy** - `terraform apply` provisions VPS + deploys app

## Quick Start

```bash
cd infra/terraform

# Configure
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your API keys

# Deploy
terraform init
terraform apply
```

## Architecture

```
Client → Nginx (SSL/Rate Limit) → Docker Container → OpenAI/Claude APIs
```

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `openai_api_key` | OpenAI API key | required |
| `anthropic_api_key` | Anthropic API key | required |
| `monthly_budget_usd` | Monthly API budget | 50 |
| `complexity_threshold` | Score for Claude routing (0-1) | 0.5 |
| `domain_name` | Domain for SSL (optional) | "" |

## Endpoints

- `POST /v1/chat/completions` - Chat completions (OpenAI-compatible)
- `GET /v1/models` - List available models
- `GET /v1/stats` - Routing and cost statistics
- `GET /health` - Health check

## Security

- UFW firewall (ports 22, 80, 443 only)
- Fail2ban for SSH brute-force protection
- Let's Encrypt SSL (if domain provided)
- Nginx rate limiting
- Automatic security updates
