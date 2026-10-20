# Jad Moharam — implementation status

All 18 required APIs are implemented and covered by permission and behavior tests. [JAD_API_DOCUMENTATION.md](JAD_API_DOCUMENTATION.md) lists them. The Postman collection contains 47 ordered requests.

- [x] Service 3: create/list/detail/assign/status/notes.
- [x] Service 8: create/by-user/detail/mark-read/search/delete.
- [x] Service 9: create/list/detail/add-action/action-status/delete.
- [x] Incident lifecycle and ownership restrictions.
- [x] Notification recipient privacy, read timestamps and filters.
- [x] Ordered actions, status progression, assignment, completion and retained history.
- [x] SQLite foreign keys and parameterized SQL.
- [x] Signed JWT verification, current user status/role checks and service-key notification creation.
- [x] Audit events using Omar's interfaces; automatic assignment notification over HTTP.
- [x] Durable retry for audit/notification deliveries, with concurrent delivery claims.
- [x] Local Windows environment, separate demo fixtures and ignored secrets/tokens.
- [x] Real HTTP integration checks with Omar's Audit and Reports services.
- [x] Integrate submitted Users/Assets with id-column compatibility and shared launch; test real password login.
- [ ] Mohannad completes Vulnerabilities, Asset search, audit production and SQLAlchemy FK enforcement.
- [ ] Team confirms the read-only shared-table lookup described in integration notes.
- [ ] Confirm full-name route interpretation and optional prefix.
- [x] Actual Jad Postman and database screenshots in the student's environment.
- [x] Common report and diagrams, with responsibilities marked by full student name.
- [x] Sanitized real password-login HTTP integration evidence.
- [ ] Native Postman login evidence and final team GitHub website contribution screenshots.
- [ ] All three members attend CREATES at least three days before the deadline.
- [x] Report References explains where and why AI assistance was used.
- [ ] Final common package and Moodle uploads by all members.

Implementation completion does not substitute for the outstanding team integration and submission evidence.
