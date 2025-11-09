# Security Policy

## Sensitive Data Protection

This project handles sensitive data and implements the following security measures:

### 1. Secrets Management

**Never commit the following to git:**
- `.env` files (actual configuration)
- Telegram bot tokens
- Flask secret keys
- PIN codes
- Any private keys or certificates

**Always use:**
- `.env.example` or `.env.template` files with placeholder values
- Environment variables for all secrets
- Secure secret generation for production

### 2. Required Environment Variables

**Bot (main.py):**
- `BOT_TOKEN` - Telegram bot token from @BotFather (required)
- `STORAGE_DIR` - Absolute path to storage directory (required)

**Web Interface (web/app.py):**
- `STORAGE_DIR` - Same as bot's storage directory (required)
- `PIN_CODE` - PIN for web authentication (required, must not be '1234')
- `SECRET_KEY` - Flask session encryption key (required, must be strong random string)

### 3. Generating Secure Secrets

**For SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**For PIN_CODE:**
Use a 6-8 digit random PIN (not '1234' or sequential numbers)

### 4. Protection Mechanisms

- ✅ All `.env` files are in `.gitignore`
- ✅ Secrets are validated on startup
- ✅ Warnings issued if default values detected
- ✅ No secrets in logs (redacted output)
- ✅ Rate limiting for authentication attempts
- ✅ `.secrets.baseline` for detect-secrets scanning

### 5. Pre-commit Checks

Run before committing:

```bash
# Check for accidentally staged .env files
git status | grep -E "\.env$"

# Scan for secrets (install detect-secrets first)
detect-secrets scan --baseline .secrets.baseline

# Verify .gitignore is working
git check-ignore .env web/.env deploy/.env
```

### 6. Deployment Checklist

Before deploying to production:

- [ ] Generate strong `SECRET_KEY` (64+ character hex string)
- [ ] Set secure `PIN_CODE` (not '1234', at least 6 digits)
- [ ] Get `BOT_TOKEN` from @BotFather
- [ ] Set absolute path for `STORAGE_DIR`
- [ ] Verify `DEBUG=false` in production
- [ ] Ensure `.env` file has restricted permissions (600)
- [ ] Never commit `.env` files to version control

### 7. Reporting Security Issues

If you discover a security vulnerability:

1. **Do not** open a public issue
2. Email the maintainer directly
3. Include detailed description and steps to reproduce
4. Allow reasonable time for fix before public disclosure

### 8. Git History

This repository has been audited for secrets in git history:
- ✅ No real tokens found in commits
- ✅ Only placeholder values in templates
- ✅ `.env` files never committed

To verify yourself:
```bash
# Search for potential token patterns
git log --all -S "BOT_TOKEN=" --source

# Search for .env files in history
git log --all --full-history -- "*.env"
```

## Last Security Audit

**Date:** November 9, 2025
**Status:** ✅ No secrets found in repository
**Auditor:** Automated + Manual Review
