# Ansible Automation Platform 2.5 & 2.6 API collections (Bruno & Postman)

This repository ships **two parallel ways** to exercise **AAP** HTTP APIs from your machine: **[Bruno](https://www.usebruno.com/)** collections (plain-text `.bru` files) and **[Postman](https://www.postman.com/)** collections (importable JSON). Use whichever matches your installed **major** platform version and your preferred client.

| Location | Format | Use when |
|----------|--------|----------|
| **`bruno/aap_2.5/`** | Bruno | Your platform is **Ansible Automation Platform 2.5**. |
| **`bruno/aap_2.6/`** | Bruno | Your platform is **Ansible Automation Platform 2.6**. |
| **`postman/aap_2.5/`** (`Platform_API.postman_collection.json`, `*.postman_environment.json`) | Postman | Same as **2.5**—after importing into Postman. |
| **`postman/aap_2.6/`** (`Platform_API.postman_collection.json`, `*.postman_environment.json`) | Postman | Same as **2.6**—after importing into Postman. |

Requests and environments are the same conceptually in both tools. The **2.6** collection adds a **`legacy/`** folder for deprecated controller RBAC mirrors; **2.5** keeps the original layout. Otherwise both share the same top-level folders (`auth`, `system`, `gateway`, `controller`, `eda`, `hub`, `workflow`). Rely on [Red Hat documentation](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/) for version-specific behavior.

### Ansible Automation Platform 2.6 collection (`bruno/aap_2.6/`)

The **2.6** collection follows Red Hat’s **gateway-first** API guidance:

- **Organizations, teams, users**, and **current user (`/me`)** are called on **`/api/gateway/v1/`** under **`gateway/`** and **`system`** (gateway `me`). Deprecated **`/api/controller/v2/`** mirrors for those resources are isolated under **`legacy/`** with notes—direct controller RBAC can lag before Event-Driven Ansible and other services reflect changes.
- **Automation execution** (projects, inventories, credentials, job templates, jobs, workflow job templates, workflow approvals, controller settings, ping, dashboard, etc.) stays on **`/api/controller/v2/`** in **`controller/`**, **`workflow/`**, and the remaining **`system`** requests.
- Set **`organizationId`**, **`userId`**, and **`teamId`** from **gateway** list/detail responses when driving gateway URLs (IDs may not match legacy controller primary keys).

Browse **`https://<host>/api/gateway/v1/`** when your deployment exposes the HTML API browser. Deprecation context: [AAP 2.6 · Deprecated features](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/html/release_notes/aap-2-6-deprecated-features).

## Prerequisites

- Network access to your AAP **platform** URL (the host that serves the unified UI / Platform Gateway).
- A user account with sufficient RBAC for the operations you try (admin for settings, operator for job launch, etc.).
- **Bruno:** [Bruno](https://www.usebruno.com/) desktop app **or** **Postman:** [Postman](https://www.postman.com/) (desktop or web).

## Bruno: open a collection

1. In Bruno: **Open Collection** (folder picker).
2. Select **`bruno/aap_2.5`** or **`bruno/aap_2.6`**—the directory that contains **`bruno.json`** for that version.
3. Pick an environment: **`local`** or **`production`** (each collection ships **`environments/local.bru`** and **`environments/production.bru`**; Bruno maps names from filenames).

Environment definitions live under **`environments/`** in the opened collection (`bruno/aap_2.5/environments/*.bru` or `bruno/aap_2.6/environments/*.bru`).

## Postman: import the collection

1. In Postman: **Import** → upload **`postman/aap_2.5/Platform_API.postman_collection.json`** or **`postman/aap_2.6/Platform_API.postman_collection.json`** (match your AAP major version).
2. **Import** the matching environment(s) from the same directory — e.g. **`postman/aap_2.5/local.postman_environment.json`** and **`postman/aap_2.5/production.postman_environment.json`** (or the **`aap_2.6/`** counterparts).
3. Select the active **environment** in the environment dropdown (so `{{baseUrl}}`, `{{token}}`, etc. resolve).

Postman requests mirror the Bruno folders (`auth`, `controller`, …). Descriptions from Bruno **`docs`** blocks are attached to each request. The **create PAT** and **create hub token** requests include **Tests** scripts that set **`token`** and **`hubToken`** on the **active environment** when the response succeeds (same idea as Bruno’s `bru.setVar`).

### Regenerating Postman from Bruno

If you edit `.bru` files and want Postman JSON to stay in sync:

```bash
python3 scripts/bruno_to_postman.py
```

That overwrites the files under **`postman/aap_2.5/`** and **`postman/aap_2.6/`** from **`bruno/aap_2.5`** and **`bruno/aap_2.6`**.

## Configure environments

**Bruno:** edit **`environments/local.bru`** for everyday lab defaults, or **`environments/production.bru`** for a second named profile (same variable keys—override **`baseUrl`**, **`username`**, **`password`**, tokens, and IDs for each deployment).

**Postman:** open **Environments**, pick the imported environment, and edit the same variable keys (or re-import JSON after changing the source `.bru` files and running the script above).

Bruno picks up environment names from the **filename** (`local.bru` → **local**, `production.bru` → **production**). Do **not** add a top-level `meta { … }` block to environment files—[official examples](https://docs.usebruno.com/variables/environment-variables) use **only** a `vars { … }` block, and Bruno **3.x** may refuse to load environments that include `meta`.

Use **`{{baseUrl}}`**, **`{{username}}`**, and **`{{password}}`** in requests as usual.

**Editing Bruno environments on disk (`environments/*.bru`) or in the UI:** set **`baseUrl`** to a plain **`https://…`** URL—**no surrounding `"` characters**. Bruno often treats those quotes as part of the stored value, so requests become **`"https://host"...`** and fail. Use the same rule for **`username`** and **`password`** (no **`"`** wrappers). **No trailing slash** on **`baseUrl`**.

**Secrets:** we do **not** rely on committing real secrets in git. After opening the Bruno collection, mark **`password`**, **`token`**, and **`hubToken`** as secrets in the Bruno UI when needed (that may add a **local-only** `vars:secret` stanza on disk). Some repo snapshots include `vars:secret` placeholders for **`password`** (and sometimes **`token`**) to document sensitive keys without values. Postman imports mark those variables with type **`secret`** where the Bruno file declares them.

### `local` vs `production`

Same keys by design; treat **`production`** as your alternate profile (real host, PATs, Hub tokens) and keep **`local`** aligned with disposable lab values.

Start with the standard connection variables:

### `local` environment (defaults)

The **`baseUrl`**, **`username`**, and **`password`** entries are prefilled for quickstarts (`https://your-aap-host.example.com`, `admin`, `changeme`)—change them before hitting a real system.

### `production` environment

Typically override **`baseUrl`**, **`username`**, **`password`**, generated **`token`** / **`hubToken`**, and resource IDs for your deployment. Prefer secret toggles (Bruno) or Postman’s secret type for sensitive values rather than committing them.

| Variable | Purpose |
|----------|---------|
| `baseUrl` | Platform URL, **no trailing slash**. Plain **`https://…`** text in **`.bru`** files and Bruno—**no `"…"`** around the URL. |
| `username` | Gateway Basic-auth login—plain text, **no `"…"`** in the UI or stored value. |
| `password` | Plain text (or secret store)—**no `"…"`** around the password value. |
| `token` | **Platform Gateway** OAuth2 / personal access token (Bearer). Filled automatically by the create-token request, or paste from the UI. |
| `hubToken` | **Private Automation Hub** token (`Authorization: Token …`). Filled by **Hub → Create hub API token**, or paste from Hub UI. |
| `organizationId`, `userId`, `teamId` | Gateway **`/api/gateway/v1/`** path segments — on **`bruno/aap_2.6`** copy from **gateway** list/detail responses (IDs may differ from legacy controller keys). |
| `jobTemplateId`, `jobId`, `inventoryId`, … | Controller **`/api/controller/v2/`** resource IDs—copy from controller list responses. |
| `edaProjectId`, `edaActivationId`, `rulebookId` | EDA resource IDs. |
| `workflowApprovalId` | Controller workflow approval step ID. |

Treat **`password`**, **`token`**, and **`hubToken`** as sensitive on real systems—toggle Bruno secrets locally, use Postman secrets, or scrub values before pushing commits from **`production`** sources.

## Recommended authentication flow (Bruno & Postman)

1. **`auth/01_create-personal-access-token`** (folder **auth** in Postman)  
   Uses HTTP Basic (`username` / `password`) against **`POST /api/gateway/v1/tokens/`**.  
   On success, Bruno scripts and Postman **Tests** store the value in **`token`**.

2. **Gateway** (organizations, teams, users), **controller** (automation resources), **EDA**, **workflow**, and most **system** checks — use **`Authorization: Bearer {{token}}`**. On **2.6**, **`system/02_me`** calls **`/api/gateway/v1/me/`**; deprecated controller RBAC mirrors live under **`legacy/`** (Postman: **legacy** folder on the 2.6 collection only).

3. **`hub/01_create-hub-token`**  
   Sends **`Authorization: Bearer {{token}}`** to **`POST /api/galaxy/v3/auth/token/`** and stores the Hub token in **`hubToken`**.

4. **Other Hub requests**  
   Use the header **`Authorization: Token {{hubToken}}`** (Galaxy NG style—not “Bearer”).

If your administrators disabled **gateway Basic auth**, skip step 1 and create a PAT in the Platform UI, then paste it into **`token`**. Create or paste a Hub token into **`hubToken`** when working only with Hub.

## What each folder contains

| Folder | Base path | Auth |
|--------|-----------|------|
| **auth** | `/api/gateway/v1/` | Basic (token creation / list) |
| **system** | Mostly `/api/controller/v2/` (`ping`, `dashboard`, `settings`). **2.6** routes **`Current user — gateway (me)`** through **`/api/gateway/v1/me/`**. | Bearer `token` |
| **gateway** | `/api/gateway/v1/` | Bearer `token` |
| **controller** | `/api/controller/v2/` | Bearer `token` |
| **legacy** | `/api/controller/v2/` | **2.6 only.** Deprecated RBAC mirrors (orgs/users/teams/`me`). Bearer `token`. |
| **eda** | `/api/eda/v1/` | Bearer `token` |
| **hub** | `/api/galaxy/v3/` | Hub: `Token {{hubToken}}`; token exchange uses Bearer `token` |
| **workflow** | `/api/controller/v2/` (approvals) | Bearer `token` |

These collections use **gateway** and **controller** URL prefixes rather than older Tower-only **`/api/v2/`** paths. Confirm exact routes against the docs for **your** AAP minor release if something returns `404`.

## TLS and self-signed certificates

If the platform uses a corporate or self-signed CA, either trust the CA at the OS level or disable SSL verification for this collection in your client’s preferences/settings (Bruno or Postman; suitable for lab use only).

## Hub on a different hostname

Some deployments expose **Private Automation Hub** on another DNS name than the gateway. Variables in the **host** portion of the URL are not split into a second base URL automatically. Options:

- Duplicate the Hub requests and change the host to your Hub URL, or  
- Add a second environment that sets `baseUrl` to the Hub host **only** for Hub calls (keep a separate copy/Duplicate of Hub requests if that is easier), or in Postman duplicate the Hub folder and edit **url**.

## Discovering endpoints

- **Gateway:** browse **`https://<host>/api/gateway/v1/`** when permitted (especially on **2.6**).
- **EDA:** run **`eda/01_openapi-json`** and open the downloaded JSON in an OpenAPI viewer, or in a browser go to  
  `https://<host>/api/eda/v1/docs/` when your install exposes it.
- **Controller:** browse  
  `https://<host>/api/controller/v2/` in a browser (when permitted)—the HTML API browser lists resources and filters.

## Troubleshooting

| Symptom | Things to check |
|--------|------------------|
| `401` on controller after login | Regenerate **`token`**; confirm clock skew; confirm user still exists and is not SSO-only without token rights. |
| Hub calls `401` | Run **Create hub API token** again; Hub tokens expire—paste a fresh token from the Hub UI if needed. |
| `404` on a Hub path | Hub layout can vary slightly by version; use Hub’s OpenAPI or UI network tab to adjust the path in a duplicated request. |
| `403` on approve | User lacks permission on that workflow or approval step. |
| `"JSON parse error"` / **`Expecting value: line 1 column 1`** on **`POST …/tokens/`** (Bruno) | Bruno **3.x** must send a literal **`{}`** body with **`Content-Type: application/json`**. Ensure **`auth/01_create-personal-access-token`** uses the multiline **`body:json { { } }`** block (pull latest collection)—a one-line **`body:json {}`** can ship an empty body and the gateway rejects it. Postman exports use a raw JSON body—if you change that request, keep a JSON object body. |
| Environment missing or empty picker (Bruno **3.x**) | Open the **`bruno/aap_2.5/`** or **`bruno/aap_2.6/`** folder that contains **`bruno.json`** (not only the parent repo root). Ensure environment `.bru` files contain **only** `vars { … }` (and optional `vars:secret [ … ]`)—remove any stray `meta` blocks if you added them manually. Reload the collection or quit Bruno fully and reopen. Clear stale secrets: temporarily rename **`production.bru`**, confirm **`local`** appears, then restore—see [secret/decrypt issues](https://github.com/usebruno/bruno/issues/5154). |
| Variables not updating after login (Postman) | Confirm an **environment** is **selected** (not **No environment**). **Tests** run only after a response—check the **Test Results** tab for errors. |

## License / upstream

Copyright © 2026 Ton Kersten.

The Bruno collections (`**/*.bru`, `bruno.json`, and related metadata under **`bruno/`**), the Postman exports (`**/*.postman_collection.json`, `**/*.postman_environment.json` under **`postman/aap_2.5/`** and **`postman/aap_2.6/`**), the converter script **`scripts/bruno_to_postman.py`**, and documentation in this repository are licensed under **GNU General Public License v3.0 only**. See [`LICENSE`](LICENSE) for the full license text.

```text
SPDX-License-Identifier: GPL-3.0-only
```

These collections are convenience wrappers around **Red Hat AAP** public API behavior; refer to the product documentation for authoritative API and security guidance:

- [Red Hat Ansible Automation Platform 2.5](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.5/)
- [Red Hat Ansible Automation Platform 2.6](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/)

Bruno and Postman are separate products. Red Hat Ansible Automation Platform, its APIs, and its documentation are **not** covered by this repository’s GPL — only this repo’s collection files and docs here are.
