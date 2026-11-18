# Testing report

The backend integration tests exercise separate student/admin sessions, password handling, profile storage, listings for all six modules, module request/response flows, notification delivery, opportunity publishing permissions, bookmarks, issue assignment/status history, user moderation and upload validation. Run them with `python -m unittest discover -s tests -v`.

Browser automation, physical Android/tablet testing, PWA installation, SMTP delivery, production persistence across restarts, release APK signing, Windows installer creation and deployment were not run. Those require a browser/device, mail configuration, Android build tools, a Windows packager or a provisioned hosting environment. The integration suite is not a substitute for those checks.
