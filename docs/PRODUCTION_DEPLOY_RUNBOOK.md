# Production Deploy Runbook — Security Hardening Rollout

Covers the CORS, encryption-key, rate-limiting, Bridge KDF, and cookie-based
auth changes across `backend/`, `bridge/`, and `rfinance_frontend/`.

## Phase 0 — Pre-flight (do this before touching anything)

1. **Backup every database**: the master Postgres DB, and each tenant's
   local Bridge Postgres DB. Non-negotiable — this rollout touches
   encryption keys.
2. **Audit the `tenants` table** in the master DB: for each tenant, confirm
   `subdomain` and `custom_domain` exactly match their real live domain
   (case, `www.` prefix, no trailing slash). The new CORS middleware will
   silently block any tenant whose stored value doesn't match what the
   browser sends as `Origin`.
3. **Note the current `ENCRYPTION_KEY`**: check what's actually live in
   production's env file right now. If it was never overridden, it's still
   the hardcoded default (`change-this-to-a-secure-32-byte-base64-key-in-production`)
   — that's the `OLD_ENCRYPTION_KEY` for the migration.
4. **Pick a maintenance window** and notify users: everyone will be logged
   out once (cookie-based auth replaces localStorage tokens).

---

## Phase 1 — Master Backend (one-time, single deploy)

1. Deploy the new backend code.
2. `pip install -r requirements.txt` (pulls in `slowapi`).
3. **Encryption key rotation — do this before flipping traffic to the new key:**
   - Set `ENCRYPTION_KEY` (new value) in the real production env file.
   - Run `python scripts/rotate_encryption_key.py` with
     `OLD_ENCRYPTION_KEY=<the old hardcoded default>` set, in an
     environment where the new `ENCRYPTION_KEY` is already loaded. This
     decrypts every affected field with the old key and re-encrypts with
     the new one, in place.
   - Spot-check: pull an IA Master record and an email SMTP setting from
     the DB/API afterward and confirm they display correctly, not as
     garbled ciphertext.
4. Set `FLOWER_USER` / `FLOWER_PASSWORD` in the real env file; confirm
   Flower is now bound to `127.0.0.1` only.
5. Confirm Redis is reachable from the backend container — check startup
   logs for the "falling back to in-memory" warning. If it appears in
   prod, rate limiting won't be consistent across replicas; fix Redis
   connectivity before relying on it.
6. Restart/redeploy the backend.
7. Smoke test: super admin login, one IA login from their real custom
   domain (checks CORS), hit `/auth/login` a few times fast (checks rate
   limit doesn't false-positive on normal use).

---

## Phase 2 — Frontend (one-time, single deploy)

1. Deploy the new frontend build. Backend-first-then-frontend is fine —
   the backend's login response format didn't change (still JSON tokens),
   so an old frontend build wouldn't break against the new backend during
   any rollout gap.
2. Open the live site in a browser, check DevTools Console for **CSP
   violations** — anything blocked under `connect-src 'self'` or
   `script-src` (analytics, embedded widgets, external fonts) needs an
   explicit allowance added to `next.config.ts`.
3. Confirm login sets `accessToken`/`refreshToken` as `HttpOnly` cookies
   (DevTools → Application → Cookies) for: super admin, an IA owner, a
   client.
4. Confirm an already-logged-in user (old localStorage session) gets
   cleanly redirected to `/login` rather than stuck in a broken state.

---

## Phase 3 — Bridge: repeat once per tenant

Each Bridge is an independent deployment with its own server and DB, so
treat it as a separate mini-rollout per tenant. **Do them one at a time,
not all simultaneously** — finish and verify one tenant fully before
touching the next. This is safe because Bridge's new `decrypt_string` is
backward-compatible: it tries the new PBKDF2 key, then falls back to the
old unsalted SHA-256 derivation, then legacy padding — so **existing data
keeps working without any forced re-encryption**.

| Step | Action |
|---|---|
| 1 | Backup that tenant's local Postgres DB |
| 2 | Deploy new Bridge code (`auth.py`, `encryption.py`, `registration.py`, `setup_routes.py`) |
| 3 | Restart the Bridge service |
| 4 | Log in to that tenant's portal, confirm client names/PAN/etc. still display correctly (proves old-key fallback decryption works) |
| 5 | *(Optional, non-urgent)* Run `scripts/rotate_encryption_kdf.py` to proactively re-encrypt existing PII under the stronger PBKDF2 key — fast thanks to the caching fix, safe to run anytime, not required to keep the tenant working |
| 6 | Confirm `.env` permissions tightened (`ls -l .env` / `icacls .env`) |
| 7 | Cross-check this tenant's `subdomain`/`custom_domain` against the master `tenants` table from Phase 0 — a mismatch here means CORS silently blocks this specific tenant even though Bridge is healthy |
| 8 | Full smoke test: owner login, clients list loads, IA master profile loads, document upload/download, one test email send (exercises SMTP password decrypt) |

Track progress:

```
[ ] Tenant 1 — DB backup / deploy / restart / verify / (rotate KDF) / .env perms / domain check / smoke test
[ ] Tenant 2 — same
[ ] Tenant 3 — same
[ ] Tenant 4 — same
[ ] Tenant 5 — same
```

---

## Rollback notes

- **Frontend**: safe to roll back anytime — stateless, worst case users
  log in once more.
- **Backend**: safe to roll back **before** running the encryption key
  migration. Once the migration has run and you've confirmed the app
  works with the new key, don't revert `ENCRYPTION_KEY` in the env file —
  that would break decryption of everything re-encrypted since.
- **Bridge**: safe to roll back **only if no new data was written since
  the upgrade** on that tenant. If a client record was created/edited
  after the Bridge upgrade, it may have been encrypted with the new
  PBKDF2 derivation — rolling back to old Bridge code (which doesn't know
  PBKDF2) would make that specific data undecryptable until the new code
  is redeployed. In practice: if a tenant's Bridge needs to roll back,
  roll forward again rather than staying on old code for long.
