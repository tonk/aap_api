# Bruno collections: Ansible Automation Platform 2.5 & 2.6 APIs

This repository contains two separate [Bruno](https://www.usebruno.com/) collections for exercising **AAP** HTTP APIs from your machine:

| Directory | Use when |
|-----------|-----------|
| **`aap_2.5/`** | Your platform is **Ansible Automation Platform 2.5**. |
| **`aap_2.6/`** | Your platform is **Ansible Automation Platform 2.6**. |

Requests stay local; each collection is plain text files (`.bru`) you can track in git. **`aap_2.6`** adds a **`legacy/`** folder for deprecated controller RBAC mirrors; **`aap_2.5`** keeps the original flat layout. Otherwise both collections share the same top-level folders (`auth`, `system`, `gateway`, `controller`, `eda`, `hub`, `workflow`). Open the collection that matches your installed major version and rely on [Red Hat documentation](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/) for version-specific behavior.

### Ansible Automation Platform 2.6 collection (`aap_2.6/`)

The **2.6** collection follows Red Hat’s **gateway-first** API guidance:

- **Organizations, teams, users**, and **current user (`/me`)** are called on **`/api/gateway/v1/`** under **`gateway/`** and **`system`** (gateway `me`). Deprecated **`/api/controller/v2/`** mirrors for those resources are isolated under **`legacy/`** with notes—direct controller RBAC can lag before Event-Driven Ansible and other services reflect changes.
- **Automation execution** (projects, inventories, credentials, job templates, jobs, workflow job templates, workflow approvals, controller settings, ping, dashboard, etc.) stays on **`/api/controller/v2/`** in **`controller/`**, **`workflow/`**, and the remaining **`system`** requests.
- Set **`organizationId`**, **`userId`**, and **`teamId`** from **gateway** list/detail responses when driving gateway URLs (IDs may not match legacy controller primary keys).

Browse **`https://<host>/api/gateway/v1/`** when your deployment exposes the HTML API browser. Deprecation context: [AAP 2.6 · Deprecated features](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/html/release_notes/aap-2-6-deprecated-features).

## Prerequisites

- [Bruno](https://www.usebruno.com/) installed (desktop app).
- Network access to your AAP **platform** URL (the host that serves the unified UI / Platform Gateway).
- A user account with sufficient RBAC for the operations you try (admin for settings, operator for job launch, etc.).

## Open a collection

1. In Bruno: **Open Collection** (folder picker).
2. Select **`aap_2.5`** or **`aap_2.6`**—the directory that contains **`bruno.json`** for that version.
3. Pick an environment: **`local`** or **`production`** (each collection ships **`environments/local.bru`** and **`environments/production.bru`**; Bruno maps names from filenames).

Environment definitions live under **`environments/`** in the opened collection (`aap_2.5/environments/*.bru` or `aap_2.6/environments/*.bru`).

## Configure environments

Edit **`environments/local.bru`** for everyday lab defaults, or **`environments/production.bru`** when you want a second named profile (same variable keys—override **`baseUrl`**, **`username`**, **`password`**, tokens, and IDs for each deployment).

Bruno picks up environment names from the **filename** (`local.bru` → **local**, `production.bru` → **production**). Do **not** add a top-level `meta { … }` block to these files—[official examples](https://docs.usebruno.com/variables/environment-variables) use **only** a `vars { … }` block, and Bruno **3.x** may refuse to load environments that include `meta`.

**Secrets:** we do **not** ship `vars:secret [ … ]` blocks in git (secrets plus decryption bugs has historically hidden environments on reopen—see [discussion around Bruno decrypt fixes](https://github.com/usebruno/bruno/issues/3479)). After opening the collection, mark **`password`**, **`token`**, and **`hubToken`** as secrets in the Bruno UI when needed (that may add a **local-only** `vars:secret` stanza on disk).

### `local.bru` vs `production.bru`

Same keys by design; treat **`production`** as your alternate profile (real host, PATs, Hub tokens) and keep **`local`** aligned with disposable lab values.

Start with the standard connection variables:

### `local.bru` (defaults)

The **`baseUrl`**, **`username`**, and **`password`** entries are prefilled for quickstarts (`https://aap.example.com`, `admin`, `changeme`)—change them before hitting a real system.

### `production.bru`

Typically override **`baseUrl`**, **`username`**, **`password`**, generated **`token`** / **`hubToken`**, and resource IDs for your deployment. Prefer Bruno’s secret toggle for sensitive values rather than committing them.


| Variable | Purpose |
|----------|---------|
| `baseUrl` | Platform URL, **no trailing slash** (defaults to `https://aap.example.com`; replace with your host). |
| `username` | Login name for gateway Basic auth when minting a PAT (defaults to `admin`). |
| `password` | Password for Basic auth when minting a PAT (defaults to `changeme` in git copies—change before use). Use Bruno’s secret toggle on **`production`** when storing real passwords. |
| `token` | **Platform Gateway** OAuth2 / personal access token (Bearer). Filled automatically by the create-token request, or paste from the UI. |
| `hubToken` | **Private Automation Hub** token (`Authorization: Token …`). Filled by **Hub → Create hub API token**, or paste from Hub UI. |
| `organizationId`, `userId`, `teamId` | Gateway **`/api/gateway/v1/`** path segments — on **`aap_2.6`** copy from **gateway** list/detail responses (IDs may differ from legacy controller keys). |
| `jobTemplateId`, `jobId`, `inventoryId`, … | Controller **`/api/controller/v2/`** resource IDs—copy from controller list responses. |
| `edaProjectId`, `edaActivationId`, `rulebookId` | EDA resource IDs. |
| `workflowApprovalId` | Controller workflow approval step ID. |

Treat **`password`**, **`token`**, and **`hubToken`** as sensitive on real systems—toggle Bruno secrets locally or scrub values before pushing commits from **`production.bru`**.

## Recommended authentication flow

1. **`auth/01_create-personal-access-token`**  
   Uses HTTP Basic (`username` / `password`) against **`POST /api/gateway/v1/tokens/`**.  
   On success, a script stores the value in **`token`**.

2. **Gateway** (organizations, teams, users), **controller** (automation resources), **EDA**, **workflow**, and most **system** checks — use **`Authorization: Bearer {{token}}`**. On **`aap_2.6`**, **`system/02_me`** calls **`/api/gateway/v1/me/`**; deprecated controller RBAC mirrors live under **`legacy/`**.

3. **`hub/01_create-hub-token`**  
   Sends **`Authorization: Bearer {{token}}`** to **`POST /api/galaxy/v3/auth/token/`** and stores the Hub token in **`hubToken`**.

4. **Other Hub requests**  
   Use the header **`Authorization: Token {{hubToken}}`** (Galaxy NG style—not “Bearer”).

If your administrators disabled **gateway Basic auth**, skip step 1 and create a PAT in the Platform UI, then paste it into **`token`**. Create or paste a Hub token into **`hubToken`** when working only with Hub.

## What each folder contains

| Folder | Base path | Auth |
|--------|-----------|------|
| **auth** | `/api/gateway/v1/` | Basic (token creation / list) |
| **system** | Mostly `/api/controller/v2/` (`ping`, `dashboard`, `settings`). **`aap_2.6`** routes **`Current user — gateway (me)`** through **`/api/gateway/v1/me/`**. | Bearer `token` |
| **gateway** | `/api/gateway/v1/` | Bearer `token` |
| **controller** | `/api/controller/v2/` | Bearer `token` |
| **legacy** | `/api/controller/v2/` | **`aap_2.6` only.** Deprecated RBAC mirrors (orgs/users/teams/`me`). Bearer `token`. |
| **eda** | `/api/eda/v1/` | Bearer `token` |
| **hub** | `/api/galaxy/v3/` | Hub: `Token {{hubToken}}`; token exchange uses Bearer `token` |
| **workflow** | `/api/controller/v2/` (approvals) | Bearer `token` |

These collections use **gateway** and **controller** URL prefixes rather than older Tower-only **`/api/v2/`** paths. Confirm exact routes against the docs for **your** AAP minor release if something returns `404`.

## TLS and self-signed certificates

If the platform uses a corporate or self-signed CA, either trust the CA at the OS level or disable SSL verification for this collection in Bruno’s preferences/settings for that environment (suitable for lab use only).

## Hub on a different hostname

Some deployments expose **Private Automation Hub** on another DNS name than the gateway. Bruno does not expand variables inside the host portion of URLs from a second base URL automatically. Options:

- Duplicate the Hub requests and change the host to your Hub URL, or  
- Add a second Bruno environment that sets `baseUrl` to the Hub host **only** for Hub calls (keep a separate collection copy of Hub requests if that is easier).

## Discovering endpoints

- **Gateway:** browse **`https://<host>/api/gateway/v1/`** when permitted (especially on **`aap_2.6`**).
- **EDA:** run **`eda/01_openapi-json`** and open the downloaded JSON in an OpenAPI viewer, or in a browser go to  
  `https://<host>/api/eda/v1/docs/` when your install exposes it.
- **Controller:** browse  
  `https://<host>/api/controller/v2/` in a browser (when permitted)—the HTML API browser lists resources and filters.

## Troubleshooting

| Symptom | Things to check |
|--------|------------------|
| `401` on controller after login | Regenerate **`token`**; confirm clock skew; confirm user still exists and is not SSO-only without token rights. |
| Hub calls `401` | Run **Create hub API token** again; Hub tokens expire—paste a fresh token from the Hub UI if needed. |
| `404` on a Hub path | Hub layout can vary slightly by version; use Hub’s OpenAPI or UI network tab to adjust the path in a duplicated `.bru` file. |
| `403` on approve | User lacks permission on that workflow or approval step. |
| Environment missing or empty picker (Bruno **3.x**) | Open the **`aap_2.5/`** or **`aap_2.6/`** folder that contains **`bruno.json`** (not the parent repo). Ensure environment `.bru` files contain **only** `vars { … }`—remove any stray `meta` blocks if you added them manually. Reload the collection or quit Bruno fully and reopen. Clear stale secrets: temporarily rename **`production.bru`**, confirm **`local`** appears, then restore—see [secret/decrypt issues](https://github.com/usebruno/bruno/issues/5154). |

## License / upstream

Copyright © 2026 Ton Kersten.

The Bruno collections in this repository (`.bru` files, `bruno.json`, and related metadata) are licensed under **GNU General Public License v3.0 only**. See [`LICENSE`](LICENSE) for the full license text.

```text
SPDX-License-Identifier: GPL-3.0-only
```

These collections are convenience wrappers around **Red Hat AAP** public API behavior; refer to the product documentation for authoritative API and security guidance:

- [Red Hat Ansible Automation Platform 2.5](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.5/)
- [Red Hat Ansible Automation Platform 2.6](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/)

Bruno itself is separate open-source software. Red Hat Ansible Automation Platform, its APIs, and its documentation are **not** covered by this repository’s GPL — only this repo’s collection files and docs here are.
