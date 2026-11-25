# CampusOne API

All JSON endpoints use same-origin Flask session cookies (`HttpOnly`, `SameSite=Lax`). Sign in first. Error responses use `{"error":"..."}` and suitable HTTP codes. The web frontend uses the same routes.

| Method | Route | Access | Purpose |
|---|---|---|---|
| GET | `/api/health` | public | Health check |
| POST | `/api/auth/register` | public | Create student account; admin email is configured by environment |
| POST | `/api/auth/login` | public | Start session |
| POST | `/api/auth/logout` | public | End session |
| GET | `/api/auth/me` | signed in | Current user and profile |
| POST | `/api/auth/forgot-password` | public | Returns `501` with a clear message until email delivery is configured; no reset email is sent |
| GET, PUT | `/api/profile` | signed in | Read/update profile |
| GET, POST | `/api/{teams,tutoring,lost-found,opportunities}` | signed in; opportunities POST admin only | Search/list and create module records |
| POST | `/api/{module}/{record_id}/requests` | signed in | Send a team/tutoring request, lost-item claim or opportunity inquiry |
| GET | `/api/requests` | signed in | Requests sent to or received by the user |
| PUT | `/api/requests/{id}` | recipient or admin | Respond to request |
| POST | `/api/opportunities/{id}/bookmark` | signed in | Toggle saved opportunity |
| POST | `/api/upload` | signed in | Upload PNG/JPG/WEBP up to 5 MB |
| GET | `/api/notifications` | signed in | List in-app notifications |
| PUT | `/api/notifications/{id}/read` | owner | Mark notification read |
| GET | `/api/dashboard` | signed in | Personal activity counts |
| GET | `/api/admin/dashboard` | admin | Live counts and user list |
| PUT | `/api/admin/users/{id}` | admin | Deactivate/reactivate student account |
| PUT | `/api/admin/records/{id}` | admin | Update lost-item status and notify owner |
| GET | `/api/records/{id}/history` | owner or admin | Read status history |

Listing search accepts `q`, `category`, `department`, `status`, `mine=1`, `saved=1` (opportunities) and `match=1` (projects). Data fields are JSON on each record. Request payloads include `message`, and for tutoring sessions may include `datetime` and `mode`.

## Database

SQLite enables foreign keys and creates tables on startup. `users` and `profiles` hold accounts and student profile fields. `records` stores module listings, `links` stores requests/connections, `notifications` stores in-app alerts, `history` stores status changes, and `bookmarks` stores saved opportunities. Indexes support module/status and owner lookups. SQLite data and uploads live under `CAMPUSONE_DATA_DIR`.
