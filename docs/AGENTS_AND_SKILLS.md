# Future Agents and Skills

## Goal

Future agents should learn this project from the Markdown files in `docs/`, inspect the relevant code, run checks, and report problems in clear operator language.

## Agent Rules

- Always read `docs/PROJECT_KNOWLEDGE.md` first.
- Check the actual code before making a change.
- Never commit, push, deploy, or change production settings without explicit user permission.
- When reporting a failure, explain the likely place to check and the exact symptom.
- Keep service-specific knowledge in this file or new docs under `docs/`.

## SMS Agent

Scope:

- `template/index.html`
- `template/script.js`
- SMS routes in `app.py`
- SMS sheet `SMS`
- CGR sheet `חיפ_סמס`
- Inforu logs under `did_inforu/`

Checks:

- Load pending SMS customers from `/load-data`.
- Confirm selected customers have required fields before update.
- Confirm Domain, DID, NumberCGR, and status updates match the Google Sheet rules.
- Confirm Inforu SMS actions still call the expected backend routes.

Example alert:

`Mail Inforu stopped working. Check the Make automation webhook, confirm the webhook URL did not change, and confirm the Inforu balance/account is active.`

## Bot Agent

Scope:

- `template/bot.html`
- `template/bot.js`
- `/bot-data`
- `/bot-done`
- Google Sheet `שירות מענה - בוט`

Checks:

- Customers load from the Bot sheet.
- Done button marks column P checkbox.
- Empty message appears when no customers are waiting.

## F2M Agent

Scope:

- `template/f2m.html`
- `template/f2m.js`
- `/f2m-data`
- `/f2m-done`
- Google Sheet `m2f / f2m`

Checks:

- Customer email is present.
- Domain lookup by order works.
- Done updates status column H to `בוצע`.

## Recordings Agent

Scope:

- `template/record.html`
- `template/record.css`
- `/recordings-data`
- `/download-record/<file_id>/<domain>`
- `/mark-done/<file_id>`
- Google Drive folder configured by `DRIVE_FOLDER_ID`

Checks:

- WAV files load from the Drive folder.
- Domain is found from the order id in the filename.
- Download filename uses `<domain>_IVR.wav` when domain exists.
- Done moves the file to the Drive `Done` folder.
- Empty message appears when no recordings are waiting.

## Human Service Agent

Scope:

- `template/human_service.html`
- `template/human_service.js`
- `/human-service-data`
- `/human-service-done`
- Google Sheet `שירות מענה - אנושי`

Checks:

- Customers load only when HIP exists and column N is not checked.
- Clicking the waiting button marks column N checkbox.
- The row disappears after a successful done update.
- Empty message appears when no customers are waiting.

## Support Ticket Master Agent

Scope:

- `docs/SUPPORT_TICKET_MASTER_SKILL.md`
- `template/support_tickets.html`
- `template/support_tickets.css`
- `template/support_tickets.js`
- Support ticket routes and helpers in `app.py`
- `log/support.log`
- `Screens/TicketID####/`

Checks:

- Ticket ids are unique and formatted as `#0001`.
- New tickets use Israel time and the current creator name.
- `מרכזייה` tickets require Domain.
- JPG attachments are saved under the matching ticket folder.
- Assignment is limited to `Admin`, `Yevgeni`, and `Nir`.
- Status colors remain yellow for `Waiting` and green for `Done`.

## GitHub Expert Agent

Repository:

`https://github.com/QAEngin/sms_imported.git`

Allowed with user permission:

- Review `git status`.
- Create focused commits.
- Push to GitHub.
- Help create releases or deployment branches.

Required approval:

- `git commit`
- `git push`
- changing remotes
- deploying to cloud
- modifying production credentials or domain DNS

Suggested workflow:

1. Run `git status --short`.
2. Explain the files that changed.
3. Ask permission before commit.
4. Ask permission before push.
5. After push, report branch and commit hash.

## Production Deployment Agent

Goal:

Find a cheap but production-usable way to host the Flask app, keep secrets safe, and connect a real domain.

Good candidate paths to evaluate:

- Small VPS with systemd, Nginx, Gunicorn, and Cloudflare DNS.
- Managed container/app hosting with environment variables and HTTPS.
- Low-cost PaaS only if it supports persistent environment variables, custom domains, and reliable background-free Flask hosting.

Production checklist:

- Move secrets out of code and into environment variables.
- Keep `credentials.json` out of GitHub.
- Use HTTPS.
- Configure domain DNS through a stable DNS provider.
- Run Flask behind Gunicorn or another production WSGI server.
- Add server logs and a restart policy.
- Verify Google service account access to Sheets and Drive after deploy.

