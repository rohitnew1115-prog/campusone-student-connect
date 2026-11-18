# Testing report

Last local verification: 2026-11-18.

`python -m unittest discover -s tests -v` passed all 6 tests. Coverage includes registration/login and password hashing; Team Finder named invitations and accepted membership; tutoring and lost-item requests; opportunity permissions/bookmarks; mentor requests and notifications; issue report IDs, admin queue/status updates and owner notifications; user moderation; image upload validation; and the SQLite health endpoint.

`node --check frontend/js/app.js`, `python -m py_compile app.py tests/test_flows.py` and `git diff --check` passed.

Not run: a public deployment, external-device/browser verification, PWA installation, Android APK build/install/signing, Windows installer, email delivery, or data persistence across a production restart. The local environment has Node.js but no npm, Java or Android SDK. No production URL, APK or release has been created. These checks need a deployed HTTPS backend and a provisioned Android/build environment.
