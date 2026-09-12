# Google sign-in and Gemini on Render

## Backend web service

Use the existing Python service with root directory `backend`, build command
`pip install -r requirements.txt`, start command
`uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1`, and health path
`/api/health`.

Set these environment variables in Render:

| Variable | Value |
| --- | --- |
| `GOOGLE_CLIENT_ID` | Public Web application OAuth Client ID from Google Cloud |
| `GEMINI_API_KEY` | Enter the secret directly in Render |
| `GEMINI_MODEL` | `gemini-3.7-flash`, or an available generateContent model for your project |
| `CORS_ORIGINS` | Exact frontend origin, e.g. `https://your-site.onrender.com`; comma-separated if multiple |
| `DATABASE_URL` | Secret PostgreSQL connection string from Neon, including `sslmode=require` |

For free development, keep the existing Render static site and web service and
create a [Neon Free PostgreSQL database](https://neon.com/pricing). Copy its
connection string directly into Render's `DATABASE_URL` secret environment value.
The app accepts `postgres://`, `postgresql://`, and `postgresql+psycopg://` URLs
and creates its tables on startup. Choose a nearby region when possible.
Never commit the connection string. Free plans have quotas and can change.

Without `DATABASE_URL`, the app uses local SQLite. Render Free has an ephemeral
filesystem: SQLite account data can disappear on restart or deployment. A paid
persistent disk is an alternative (`VEDIC_DB=/var/data/vedic.db`). Switching
databases does not migrate existing accounts; back up and migrate any existing
server data before switching. Guest charts can be imported after Google sign-in.
Keep one worker and one instance: chat throttling is in memory (six attempts per
account per minute). It resets on restart and is not a daily spending limit.
Use provider quotas for an overall budget, and shared rate limiting before scaling.

## Frontend static site

Root directory `frontend`; build command `npm ci && npm run build`; publish
directory `dist`. Set `VITE_API_BASE` to the full backend origin without `/api`.
Redeploy after changing this build-time variable. Google Client ID is loaded
from the backend at runtime. Never put the Gemini key in a `VITE_` variable.

## Google setup

In Google Cloud, configure Google Auth Platform branding, audience and a client
of type **Web application**. Add the exact frontend origin to **Authorized
JavaScript origins**, plus `http://localhost:5173` for local testing (and
`http://127.0.0.1:5173` if used). Add test users when the app is in testing mode.
This integration uses the Google Identity Services popup callback and needs no
OAuth client secret or server redirect URI. Complete Google consent personally.

Create the Gemini key in Google AI Studio and enter it directly into the backend
Render environment. No credentials belong in Git or chat.

## Local verification

Copy `backend/.env.example` to `backend/.env` and fill it locally. Start from
`backend` with `python -m uvicorn app.main:app --env-file .env --port 8000`.
Run `npm run dev` from `frontend`, with `VITE_API_BASE` unset for the local proxy.

1. Sign in with Google, reload, confirm the session, then sign out.
2. Open a chart, sign in and send a Gemini question. Check the reply against the
   displayed placements; try unknown birth time as well.
3. Switch charts during a request: the prior response must not appear in the new
   conversation. Sign out: chat must be disabled and conversations cleared.
4. Verify the frontend only receives the public Client ID and your app session
   token. Gemini calls and the API key stay on the backend.

Signed-in charts save to the backend account library and load on other devices.
Guest charts remain in the browser until the user chooses Import browser charts.
The dashboard supports creation, opening and editing birth details, renaming,
and confirmed removal with session undo. Concurrent changes are rejected and
refreshed to prevent overwriting another device's edits. Chat history is kept
only for the current page session and separately for each selected chart.
Existing password accounts are preserved, but password endpoints are removed.
An email collision with a legacy account is refused rather than silently linked;
those accounts need an explicit ownership-verified migration by the site owner.

Live Google consent and Gemini responses still require configured credentials.
Automated tests mock provider calls and do not establish live service availability.

References: [Google token verification](https://developers.google.com/identity/gsi/web/guides/verify-google-id-token),
[Gemini generateContent](https://ai.google.dev/api/generate-content),
[Render configuration](https://render.com/docs/blueprint-spec).

Free development limits: [Render Free](https://render.com/docs/free) sleeps after
inactivity, so the first request may be slow. [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing)
lists free-tier availability per model; verify your project's quota in AI Studio.
The app does not enable paid billing or automatically switch models. Google may
use free-tier prompts and responses to improve its products; avoid entering
private information into test conversations.
