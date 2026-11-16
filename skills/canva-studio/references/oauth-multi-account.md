# Canva MCP OAuth 2.0 PKCE & Multi-Account Rotation

## Endpoints & Metadata
* **Discovery Metadata:** `https://mcp.canva.com/.well-known/oauth-authorization-server`
* **MCP RPC Endpoint:** `https://mcp.canva.com/mcp` (`Accept: application/json, text/event-stream`)
* **OAuth Authorize:** `https://mcp.canva.com/authorize`
* **OAuth Token Exchange / Refresh:** `https://mcp.canva.com/token`
* **Dynamic Client Registration (RFC 7591):** `https://mcp.canva.com/register`
* **Scopes:** `profile:read design:meta:read design:content:write design:content:read asset:read asset:write folder:read brandkit:read`

> Always exchange authorization codes and refresh expired tokens against `https://mcp.canva.com/token`, never `https://api.canva.com/rest/v1/oauth/token`, for MCP-scoped credentials.

## Credential Resolution Order
1. Environment variables: `CANVA_CLIENT_ID` and `CANVA_CLIENT_SECRET` (optional).
2. Cached dynamic registration: `<CANVA_STATE_DIR>/canva_client.json` (defaults to `~/.canva-skills-mcp/canva_client.json`).
3. Automatic RFC 7591 registration against `https://mcp.canva.com/register` when neither env vars nor cached client credentials exist.

## Multi-Account Storage Layout
Under `CANVA_STATE_DIR` (default `~/.canva-skills-mcp`):
* `canva_accounts.json` — Registry tracking `active_account_id`, account metadata, token file paths, and `last_cooldown_ends_at`.
* `canva_token.json` — Active primary account token mirror.
* `canva_token_<account_id>.json` — Per-account token files (`account_2`, `account_3`, etc.).

## Zero-Cooldown Rotation Behavior
1. On `401 Unauthorized`, automatically refresh the active account's `access_token` using its `refresh_token` and retry once.
2. On `quota_cooldown` (`_meta.com.canva/aiCreditQuotaError.quota_usage.cooldown_ends_at`), record the cooldown expiry timestamp, rotate to the next connected account whose cooldown has elapsed, and immediately re-dispatch the MCP call without blocking for 180–300 seconds.
