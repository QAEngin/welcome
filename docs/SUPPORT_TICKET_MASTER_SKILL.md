# Support Ticket Master Skill

## Purpose

Use this guide when working on the Support Tickets page or when an agent needs to reason over local support ticket history.

## Scope

- `app.py` support-ticket helpers and routes
- `template/support_tickets.html`
- `template/support_tickets.css`
- `template/support_tickets.js`
- `log/support.log`
- `Screens/TicketID####/`

## Ticket Store

Tickets are stored as JSON lines in `log/support.log`. Each line is one ticket object.

Important fields:

- `id`: numeric ticket id.
- `ticket_id`: display id generated from `id`, for example `#0001`.
- `created_at`: ISO timestamp in Israel time.
- `created_at_display`: operator-facing timestamp.
- `creator`: one of the support users or the current session name.
- `ticket_type`: Hebrew type, one of `תקלה`, `שאלה`, `שירות`, `נוסף`.
- `service_type`: selected or free text service value.
- `domain`: required only when service type is `מרכזייה`.
- `priority`: `High`, `Medium`, or `Low`.
- `description`: free text, Hebrew supported.
- `status`: `Waiting` or `Done`.
- `assigned_to`: empty or one of `Admin`, `Yevgeni`, `Nir`.
- `attachments`: JPG metadata, stored under `Screens/TicketID####/`.
- `updates`: audit trail for status and assignment changes.

## Operating Rules

- Never renumber existing tickets.
- New ticket ids must be the next number after the highest existing `id`.
- Preserve Hebrew text as UTF-8.
- Keep attachment paths relative and validate folder names as `TicketID####`.
- Only accept `.jpg` and `.jpeg` uploads unless the product owner asks for more file types.
- Status color meaning: `Waiting` is yellow, `Done` is green.
- Priority color meaning: `High` is red, `Medium` is orange, `Low` is green.

## Manual Checks

1. Open `/support-tickets`.
2. Confirm All Tickets, My Tickets, and Unassigned filters load.
3. Create a ticket with service type `מרכזייה` and verify Domain is required.
4. Create a ticket with a JPG and verify it appears under `Screens/TicketID####/`.
5. Assign a ticket to `Admin`, `Yevgeni`, or `Nir`.
6. Change status to `Done` and confirm it turns green.
