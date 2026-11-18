# Installation and deployment guide

## Local demonstration

Follow the README Windows setup. Keep the `.env` secret private. The configured `CAMPUSONE_ADMIN_EMAIL` receives the admin role at registration; select that role only for a campus-controlled account. SQLite and upload directories are created automatically.

## PWA

Serve through HTTPS for install support on desktop and mobile. Open the app in a supported browser and select Install. On iOS, use Safari's Share menu and Add to Home Screen. The service worker caches the application shell only; API actions require a connection. The offline fallback returns the cached app shell, with no offline data writes.

## Android

Install Node.js and Android Studio/SDK, then run `npm install`, `npx cap add android`, and `npx cap sync android`. Open the generated `android/` folder in Android Studio, set a production HTTPS application URL/API strategy, build and sign the release APK. This repository contains the Capacitor settings but no Android SDK, generated native project or signed APK. A release APK has not been built.

## Server deployment

Build the included Dockerfile, mount a durable volume at `/data`, set `CAMPUSONE_SECRET`, `CAMPUSONE_ADMIN_EMAIL`, and `CAMPUSONE_DATA_DIR=/data`, and serve behind HTTPS. Run one worker for SQLite. Back up the database and uploads together. Check `/api/health` after deployment. Configure email delivery, request throttling, logging/monitoring, backups, privacy policy and campus enrollment rules before real-world use. Deployment credentials and a hosting account were not available in the development workspace.
