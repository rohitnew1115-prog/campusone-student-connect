# Database design

SQLite is the only database. `app.py` initializes the schema and enables `PRAGMA foreign_keys=ON` on each connection.

| Table | Role | Main relationships |
|---|---|---|
| `users` | Account, password hash and student/admin role | Parent of profiles, records, notifications, requests and history |
| `profiles` | Department, year, skills, interests, availability and bio | One row per user |
| `records` | Project, tutor, item and opportunity listings with module JSON details | Owned by user; parent of request links and status history |
| `links` | Team invitations, tutoring requests, claims and opportunity inquiries | Links a record, sender and recipient; unique request per sender/listing/type |
| `notifications` | In-app alerts with read state | Belongs to recipient |
| `history` | Status changes and administrator resolution notes | Belongs to listing and actor |
| `bookmarks` | Saved opportunities | Composite primary key on user and listing |
| `password_resets` | Reset token hash and expiry slot | Keyed by email; email delivery not connected |

The generic `records` and `links` tables keep the four workflows on a single shared SQLite database. No student email or ID is marked as verified by this app.
