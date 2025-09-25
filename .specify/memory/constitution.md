<!--
Sync Impact Report
- Version change: n/a → 1.0.0
- Modified principles: n/a (initial ratification)
- Added sections: Core Principles (7), Additional Constraints & Non-Goals (v1), Success Criteria & Supported Platforms, Governance
- Removed sections: Template placeholders replaced
- Templates requiring updates:
	✅ .specify/templates/plan-template.md (footer path+version; gates note)
	✅ .specify/templates/spec-template.md (reviewed; no changes required)
	✅ .specify/templates/tasks-template.md (added observability category)
	⚠ README.md (not present) — add run/deploy instructions to satisfy Success Criteria
- Deferred TODOs: None
-->

# tg-collector Constitution

## Core Principles

### I. Privacy-by-default
- Store only what is needed: message text, audio file, and minimal metadata.
- Prohibit unnecessary PII: do not persist usernames, full names, phone numbers, or profile photos.
- Allowed metadata: message_id, chat_id, sender_id (if strictly required), timestamp (UTC), file size, MIME/type, sha256 checksum, and storage path.
- Redact or omit message content from logs and external outputs; logs must never contain raw audio or full text bodies.
Rationale: Minimize data footprint to reduce risk and compliance surface while enabling core functionality.

### II. Reliability (no message loss)
- Use atomic writes: write to temporary file, fsync, then rename to final path.
- Always create a paired metadata JSON alongside each payload.
- Implement clear error handling with retry limits; surface failures in logs and health check.
- Backpressure: if storage path unavailable, reject new processing and alert via logs/health.
Rationale: Filesystem-only persistence still demands durability guarantees.

### III. Transparency (safe, useful logs)
- Log structured events for received, saved, failed with stable fields: event, ts, type=text|audio, message_id, chat_id, status.
- Never log full message text or raw binary content; include sizes and checksums instead.
- Include error codes and exception types without stack traces leaking secrets.
Rationale: Operators need visibility without exposing sensitive content.

### IV. Security (defense-in-depth)
- Bot token MUST be loaded from .env (not committed); validate presence on startup.
- Strict dependency pinning (uv lockfile) and supply-chain updates via PRs.
- No arbitrary code execution; avoid eval/exec and untrusted shell calls.
- Validate MIME/type and file extension for audio; accept only Telegram voice formats (e.g., audio/ogg with Opus).
- Run as non-root, least-privilege filesystem access; set umask 027 for created files/dirs.
Rationale: Reduce attack surface for a long-running public bot.

### V. Simplicity first
- Minimal feature set: receive/save text and voice only; no DB.
- Readable, well-structured code; predictable folders and deterministic filenames.
- Prefer standard libraries; add dependencies only with clear benefit.
Rationale: Simple systems are easier to audit, operate, and secure.

### VI. Observability
- Use structured JSON logs with stable schemas.
- Provide a health check command/endpoint that returns OK plus minimal stats (uptime, queue depth, last_error_ts).
- Include startup configuration summary with redactions (e.g., token length, not value).
Rationale: Fast diagnosis without exposing secrets.

### VII. Portability
- Run via uv (Python) locally and in CI; optional Docker image.
- Provide a systemd service example for Ubuntu/Debian deployments.
- Support macOS for development and Ubuntu/Debian for production.
Rationale: Ensure frictionless dev and ops across common environments.

## Additional Constraints & Non-Goals (v1)

Constraints
- Storage: Linux filesystem only; directory layout MUST be predictable and date-partitioned.
- Filenames: deterministic pattern: {ts_utc}-{chat_id}-{message_id}-{type}.{ext}; metadata JSON shares the same stem.
- Atomicity: write to .tmp files, fsync, then rename; write metadata last only after payload persisted.
- Validation: reject unsupported MIME/types or oversized payloads (limit configurable).
- Retention: no automatic deletion in v1; document manual rotation strategy.

Non-Goals (v1)
- No database (filesystem only).
- No admin panel UI (CLI + logs only).
- No transcription/LLM features (future work).

## Success Criteria & Supported Platforms

Success Criteria
- Text and audio saved with deterministic filenames and a paired metadata JSON.
- Clear README with run and deploy instructions (macOS dev, Ubuntu/Debian prod).
- Logs confirm received/saved/failed events without leaking sensitive content.

Platforms
- Development: macOS (latest).
- Production: Ubuntu/Debian Linux servers.

## Governance

Amendment Procedure
- Propose changes via Pull Request updating this file and a brief CHANGELOG entry.
- Discuss impact; include migration notes if storage layout or log schema changes.
- Require approval from at least one maintainer; upon merge, bump version per policy.

Versioning Policy
- Semantic versioning applies to governance and principles:
	- MAJOR: Breaking changes to rules (e.g., removing a principle, redefining constraints).
	- MINOR: New principle or materially expanded guidance.
	- PATCH: Clarifications, wording, or non-semantic refinements.

Compliance & Reviews
- All PRs must include a Constitution Check section referencing the gates derived from these principles.
- CI must fail if required gates are not addressed for scope changes touching storage, logging, or security.
- Quarterly review of logs and storage samples to confirm adherence (no sensitive content persisted or logged).

**Version**: 1.0.0 | **Ratified**: 2025-09-25 | **Last Amended**: 2025-09-25