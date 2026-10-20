# Common report and evidence current version

The common report has 61 pages and covers the nine available services. All three students should use the same final team package after remaining work is finished.

## Verified current work
- Latest main and Mohannad Users/Assets/Vulnerabilities plus Asset search merged into jad-moharam, preserving original authorship.
- Jad Incidents, Notifications and Playbooks: all 18 operations implemented.
- 220 passing automated tests in 30.04 seconds, with the JUnit results included.
- New 33-request real HTTP integration: actual bcrypt password registration/login, real Assets, all three Jad services, assignment notification, reports, suspended accounts and stale roles. Passwords and bearer tokens are redacted.
- Native Postman screenshots cover all 18 Jad operations from the earlier recorded fixture run: 47 requests, 141 passing assertions. They remain historical evidence, not a claim of another native Postman run against the new team database.
- Omar real HTTP execution, both collections, SQL scripts, source archive, database snapshots, API input/output records, and historical GitHub API history views.
- The new database/real-users-assets-integration.db contains isolated test records created through the real implementation; it is not a production user database. sql/schema_team_users_assets.sql records the real model definitions. Earlier databases correspond to their original screenshot runs.

## Still required from the team
1. Mohannad reviews vulnerability lifecycle and permissions, audit events and SQLAlchemy foreign key enforcement. Only Jad connections currently enforce those keys. Vulnerabilities and Asset search are now supplied in commit 21ad9fc.
2. Omar and Mohannad connect their alert producers to the existing Notifications endpoint.
3. Supply native Postman login and Omar/remaining teammate API screenshots, and signed-in GitHub website history/contribution screenshots. Current Omar evidence and history screenshots are labeled HTTP/API views.
4. Review the Jad PR, agree on the shared database verification approach and route-name requirement, complete the remaining validation, then run final team checks and update the common report.
5. Merge after review and upload one identical complete package three times, one per student. No Moodle upload has been made.

No .env, exported token environment or live bearer token is included. The original workspace title bar is excluded from the framed Postman captures without altering response pixels.
