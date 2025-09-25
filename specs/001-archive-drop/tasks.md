# Tasks: ArchiveDrop

**Input**: Design documents from `/Users/gabby/git/no-git/SpecKitProjects/tg-collector/specs/001-archive-drop/`
**Prerequisites**: plan.md (required)

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → If not found: ERROR "No implementation plan found"
   → Extract: tech stack, libraries, structure
2. Load optional design documents:
   → data-model.md: Extract entities → model tasks
   → contracts/: Each file → contract test task
   → research.md: Extract decisions → setup tasks
   → quickstart.md: Extract scenarios → integration tests
3. Generate tasks by category:
   → Setup: project init, dependencies, linting
   → Tests: contract/integration/unit tests first (TDD)
   → Core: libraries, services, CLI/bot commands
   → Integration: logging, health, packaging
   → Polish: docs and manual QA
4. Apply task rules:
   → Different files = [P] parallel; Same file = sequential
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001, T002...)
6. Add dependency notes and parallel examples
7. Write tasks.md in feature directory
```

## Path Conventions (single-project)
- Source root: `/Users/gabby/git/no-git/SpecKitProjects/tg-collector/src/`
- Tests root: `/Users/gabby/git/no-git/SpecKitProjects/tg-collector/tests/`
- Deploy assets: `/Users/gabby/git/no-git/SpecKitProjects/tg-collector/deploy/`

## Phase 3.1: Setup
- [x] T001 Create project structure
      - Dirs: `/Users/gabby/git/no-git/SpecKitProjects/tg-collector/src/{cli,services,lib,observability}` and `/Users/gabby/git/no-git/SpecKitProjects/tg-collector/tests/{unit,integration}`
- [x] T002 Initialize uv Python project and pin deps
      - Create `pyproject.toml` and lock via uv; add deps: `aiogram`, `python-dotenv` (or equivalent), dev: `ruff`, `black`, `mypy`
- [x] T003 [P] Configure lint/format/typecheck
      - Add `.ruff.toml`, `pyproject` tool.black config, and `mypy.ini`
- [x] T004 [P] Structured JSON logger scaffold
      - File: `/Users/gabby/git/no-git/SpecKitProjects/tg-collector/src/observability/logging.py`
      - Implement get_logger(name) producing JSON logs with fields: event, ts, level, type, message_id, chat_id, status, details
- [x] T005 [P] Config loader and .env example
      - Files: `/Users/gabby/git/no-git/SpecKitProjects/tg-collector/src/config.py`, `/Users/gabby/git/no-git/SpecKitProjects/tg-collector/.env.example`, update `.gitignore` to ignore `.env`
      - Validate required env: BOT_TOKEN, STORAGE_DIR; optional: RATE_LIMIT_PER_MIN, MAX_AUDIO_BYTES, ALLOWLIST, LOG_LEVEL

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
- [x] T006 [P] Unit test: deterministic filename builder
      - File: `/Users/gabby/git/no-git/SpecKitProjects/tg-collector/tests/unit/test_naming.py`
      - Cases: builds `{ts}-{chat_id}-{message_id}-text` and `...-audio`; strips unsafe chars; stable across calls
- [x] T007 [P] Unit test: MIME/type + size validator
      - File: `/Users/gabby/git/no-git/SpecKitProjects/tg-collector/tests/unit/test_validation.py`
      - Cases: accept `audio/ogg` (opus) voice; reject unknown types; enforce `MAX_AUDIO_BYTES`
- [x] T008 [P] Integration test: save text atomically with metadata
      - File: `/Users/gabby/git/no-git/SpecKitProjects/tg-collector/tests/integration/test_storage_text.py`
      - Assert: tmp write → fsync → rename; metadata JSON fields present; checksum for text; permissions respect umask
- [x] T009 [P] Integration test: save audio (ogg) atomically with checksum
      - File: `/Users/gabby/git/no-git/SpecKitProjects/tg-collector/tests/integration/test_storage_audio.py`
      - Assert: same-stem `.ogg` + `.json`; checksum computed; metadata fields; size limits enforced
- [x] T010 [P] Integration test: per-user rate limit
      - File: `/Users/gabby/git/no-git/SpecKitProjects/tg-collector/tests/integration/test_rate_limit.py`
      - Assert: beyond quota → throttled response and log event; window resets

## Phase 3.3: Core Implementation (ONLY after tests are failing)
- [x] T011 [P] Filename/path builder
      - File: `/Users/gabby/git/no-git/SpecKitProjects/tg-collector/src/lib/naming.py`
      - `build_stem(ts_utc, chat_id, message_id, kind)` and `build_paths(base_dir, date_parts, stem, ext)`
- [x] T012 [P] MIME/type & size validation
      - File: `/Users/gabby/git/no-git/SpecKitProjects/tg-collector/src/lib/validation.py`
      - `validate_mime_and_ext(mime, ext)`; `validate_size(n_bytes, limit)`
- [x] T013 [P] Filesystem storage service (atomic)
      - File: `/Users/gabby/git/no-git/SpecKitProjects/tg-collector/src/services/storage.py`
      - Text: `save_text(chat_id, message_id, text, ts_utc)`; Audio: `save_audio(chat_id, message_id, mime, ext, data_iter, ts_utc)` with chunked writes, fsync, rename, sha256, metadata JSON
- [x] T014 [P] In-memory rate limiter (per-user)
      - File: `/Users/gabby/git/no-git/SpecKitProjects/tg-collector/src/lib/rate_limit.py`
      - Token bucket or fixed window; configurable limits from env
- [x] T015 Telegram bot with handlers
      - File: `/Users/gabby/git/no-git/SpecKitProjects/tg-collector/src/cli/bot.py`
      - aiogram polling; handlers: `/start`, `/health`, text, voice; use config, validation, storage; safe confirmations; structured logs; redacted content
- [x] T016 Error handling & logging policy
      - File: `/Users/gabby/git/no-git/SpecKitProjects/tg-collector/src/observability/logging.py` (augment) and `/Users/gabby/git/no-git/SpecKitProjects/tg-collector/src/cli/bot.py`
      - Map exceptions to error codes; never log raw text/audio; include sizes and checksums only

## Phase 3.4: Integration
- [x] T017 Wire handlers to storage service
      - Update `/Users/gabby/git/no-git/SpecKitProjects/tg-collector/src/cli/bot.py` to call storage and emit events: received, saved, failed
- [x] T018 Health check details
      - File: `/Users/gabby/git/no-git/SpecKitProjects/tg-collector/src/cli/bot.py`
      - Return "OK" with uptime, last_error_ts (nullable), session stored_count (non-sensitive)
- [ ] T019: ✅ **Finalize JSON log schema**: Complete schema documentation with stable field names, event types, and privacy compliance notes in src/observability/logging.py
      - File: `/Users/gabby/git/no-git/SpecKitProjects/tg-collector/src/observability/logging.py`
      - Ensure stable keys and levels; doc in code comments
- [x] T020 Systemd unit and docs (Linux)
      - Files: `/Users/gabby/git/no-git/SpecKitProjects/tg-collector/deploy/archive-drop.service`, `/Users/gabby/git/no-git/SpecKitProjects/tg-collector/docs/deploy/ubuntu-checklist.md`
      - Unit: non-root user, WorkingDirectory, EnvironmentFile, Restart=always, UMask=027
- [x] T021 Optional Dockerfile with uv
      - File: `/Users/gabby/git/no-git/SpecKitProjects/tg-collector/Dockerfile`
      - Minimal runtime; mounts storage; no secrets baked in

## Phase 3.5: Polish
- [x] T022 E2E integration tests
      - File: `/Users/gabby/git/no-git/SpecKitProjects/tg-collector/tests/unit/test_validation_edges.py`
- [x] T023 Comprehensive user docs
      - File: `/Users/gabby/git/no-git/SpecKitProjects/tg-collector/tests/integration/test_latency.py`
      - Targets: text ack < 1s; audio ack < 5s typical (logged timings)
- [x] T024 [P] README with run/deploy instructions
      - File: `/Users/gabby/git/no-git/SpecKitProjects/tg-collector/README.md`
      - Include uv usage, .env config, health command, folder layout, sample logs
- [x] T025 [P] Sample logs and schema
      - File: `/Users/gabby/git/no-git/SpecKitProjects/tg-collector/docs/logging.md`
      - Include redaction examples, event fields, and do/don't
- [x] T026 Manual test script
      - File: `/Users/gabby/git/no-git/SpecKitProjects/tg-collector/docs/manual-testing.md`
      - Steps for macOS dev run and Ubuntu deployment validation

## Dependencies
- Setup (T001–T005) before Tests and Core
- Tests first (T006–T010) must fail before Core (T011–T016)
- Naming/validation (T011–T012) before storage (T013)
- Storage (T013) before handlers (T015, T017)
- Logging and health (T016, T018–T019) after handlers are in place
- Packaging/docs (T020–T026) after core integration

## Parallel Execution Examples
```
# Launch unit tests together:
Task: "T006 Unit test: deterministic filename builder"
Task: "T007 Unit test: MIME/type + size validator"

# Launch core library implementations together:
Task: "T011 Filename/path builder in src/lib/naming.py"
Task: "T012 MIME/type & size validation in src/lib/validation.py"
Task: "T014 In-memory rate limiter in src/lib/rate_limit.py"

# Launch polish docs in parallel:
Task: "T024 README with run/deploy instructions"
Task: "T025 Sample logs and schema"
Task: "T026 Manual test script"
```

## Notes
- Respect Constitution v1.0.0: privacy-by-default, atomic filesystem writes, structured logs, health check, portability.
- Never log raw message text or audio. Metadata JSON uses minimal PII (numeric sender_id).
- Use umask 027 for created files/dirs and run as non-root when packaging.
