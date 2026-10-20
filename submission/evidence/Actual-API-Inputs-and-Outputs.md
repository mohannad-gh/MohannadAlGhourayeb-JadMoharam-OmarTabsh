# Actual HTTP inputs and outputs
Jad manifest includes one automatic notification call in addition to 47 Postman requests.
Authorization secrets are omitted.

## Jad Moharam 1 POST /notifications
HTTP 201 at 2026-10-20T20:19:50.259342+00:00

Request
```json
{
  "user_id": 3,
  "title": "Security alert",
  "message": "Review suspicious email",
  "type": "Security Alert",
  "severity": "High"
}
```

Response
```json
{
  "status": "success",
  "message": "Notification created",
  "warnings": [],
  "data": {
    "notification_id": 1,
    "user_id": 3,
    "title": "Security alert",
    "message": "Review suspicious email",
    "type": "Security Alert",
    "severity": "High",
    "status": "Unread",
    "created_at": "2026-10-20T20:19:50.234699Z",
    "read_at": null
  }
}
```

## Jad Moharam 2 GET /notifications/user/3
HTTP 200 at 2026-10-20T20:19:50.376378+00:00

Request
```json
null
```

Response
```json
{
  "status": "success",
  "message": "Notifications retrieved",
  "count": 1,
  "data": [
    {
      "notification_id": 1,
      "user_id": 3,
      "title": "Security alert",
      "message": "Review suspicious email",
      "type": "Security Alert",
      "severity": "High",
      "status": "Unread",
      "created_at": "2026-10-20T20:19:50.234699Z",
      "read_at": null
    }
  ]
}
```

## Jad Moharam 3 GET /notifications/1
HTTP 200 at 2026-10-20T20:19:50.400424+00:00

Request
```json
null
```

Response
```json
{
  "status": "success",
  "data": {
    "notification_id": 1,
    "user_id": 3,
    "title": "Security alert",
    "message": "Review suspicious email",
    "type": "Security Alert",
    "severity": "High",
    "status": "Unread",
    "created_at": "2026-10-20T20:19:50.234699Z",
    "read_at": null
  }
}
```

## Jad Moharam 4 PUT /notifications/1/read
HTTP 200 at 2026-10-20T20:19:50.438425+00:00

Request
```json
null
```

Response
```json
{
  "status": "success",
  "message": "Notification marked as read",
  "warnings": [],
  "data": {
    "notification_id": 1,
    "user_id": 3,
    "title": "Security alert",
    "message": "Review suspicious email",
    "type": "Security Alert",
    "severity": "High",
    "status": "Read",
    "created_at": "2026-10-20T20:19:50.234699Z",
    "read_at": "2026-10-20T20:19:50.419424Z"
  }
}
```

## Jad Moharam 5 GET /notifications/search?user_id=3&type=Security%20Alert&severity=High&status=Read
HTTP 200 at 2026-10-20T20:19:50.563832+00:00

Request
```json
null
```

Response
```json
{
  "status": "success",
  "count": 1,
  "data": [
    {
      "notification_id": 1,
      "user_id": 3,
      "title": "Security alert",
      "message": "Review suspicious email",
      "type": "Security Alert",
      "severity": "High",
      "status": "Read",
      "created_at": "2026-10-20T20:19:50.234699Z",
      "read_at": "2026-10-20T20:19:50.419424Z"
    }
  ]
}
```

## Jad Moharam 6 POST /incidents
HTTP 201 at 2026-10-20T20:19:50.657853+00:00

Request
```json
{
  "title": "Suspicious email",
  "description": "Investigate a reported phishing message",
  "category": "Phishing",
  "severity": "High",
  "reporter_id": 3,
  "asset_id": 1
}
```

Response
```json
{
  "status": "success",
  "message": "Incident created",
  "warnings": [],
  "data": {
    "incident_id": 1,
    "title": "Suspicious email",
    "description": "Investigate a reported phishing message",
    "category": "Phishing",
    "severity": "High",
    "reporter_id": 3,
    "asset_id": 1,
    "assigned_analyst_id": null,
    "status": "Open",
    "created_at": "2026-10-20T20:19:50.635848Z",
    "resolved_at": null
  }
}
```

## Jad Moharam 7 GET /incidents
HTTP 200 at 2026-10-20T20:19:50.848893+00:00

Request
```json
null
```

Response
```json
{
  "status": "success",
  "count": 1,
  "data": [
    {
      "incident_id": 1,
      "title": "Suspicious email",
      "description": "Investigate a reported phishing message",
      "category": "Phishing",
      "severity": "High",
      "reporter_id": 3,
      "asset_id": 1,
      "assigned_analyst_id": null,
      "status": "Open",
      "created_at": "2026-10-20T20:19:50.635848Z",
      "resolved_at": null
    }
  ]
}
```

## Jad Moharam 8 GET /incidents/1
HTTP 200 at 2026-10-20T20:19:50.903905+00:00

Request
```json
null
```

Response
```json
{
  "status": "success",
  "data": {
    "incident_id": 1,
    "title": "Suspicious email",
    "description": "Investigate a reported phishing message",
    "category": "Phishing",
    "severity": "High",
    "reporter_id": 3,
    "asset_id": 1,
    "assigned_analyst_id": null,
    "status": "Open",
    "created_at": "2026-10-20T20:19:50.635848Z",
    "resolved_at": null,
    "notes": []
  }
}
```

## Jad Moharam 9 POST /notifications
HTTP 201 at 2026-10-20T20:19:50.978413+00:00

Request
```json
{
  "user_id": 2,
  "title": "Incident assignment",
  "message": "You were assigned incident 1: Suspicious email",
  "type": "Incident Assignment",
  "severity": "High"
}
```

Response
```json
{
  "status": "success",
  "message": "Notification created",
  "warnings": [],
  "data": {
    "notification_id": 2,
    "user_id": 2,
    "title": "Incident assignment",
    "message": "You were assigned incident 1: Suspicious email",
    "type": "Incident Assignment",
    "severity": "High",
    "status": "Unread",
    "created_at": "2026-10-20T20:19:50.958909Z",
    "read_at": null
  }
}
```

## Jad Moharam 10 PUT /incidents/1/assign
HTTP 200 at 2026-10-20T20:19:50.986917+00:00

Request
```json
{
  "analyst_id": 2
}
```

Response
```json
{
  "status": "success",
  "message": "Incident assigned",
  "warnings": [],
  "data": {
    "incident_id": 1,
    "title": "Suspicious email",
    "description": "Investigate a reported phishing message",
    "category": "Phishing",
    "severity": "High",
    "reporter_id": 3,
    "asset_id": 1,
    "assigned_analyst_id": 2,
    "status": "Open",
    "created_at": "2026-10-20T20:19:50.635848Z",
    "resolved_at": null
  }
}
```

## Jad Moharam 11 PUT /incidents/1/status
HTTP 200 at 2026-10-20T20:19:51.154930+00:00

Request
```json
{
  "status": "Under Investigation"
}
```

Response
```json
{
  "status": "success",
  "message": "Incident status updated",
  "warnings": [],
  "data": {
    "incident_id": 1,
    "title": "Suspicious email",
    "description": "Investigate a reported phishing message",
    "category": "Phishing",
    "severity": "High",
    "reporter_id": 3,
    "asset_id": 1,
    "assigned_analyst_id": 2,
    "status": "Under Investigation",
    "created_at": "2026-10-20T20:19:50.635848Z",
    "resolved_at": null
  }
}
```

## Jad Moharam 12 PUT /incidents/1/status
HTTP 200 at 2026-10-20T20:19:51.371982+00:00

Request
```json
{
  "status": "Mitigated"
}
```

Response
```json
{
  "status": "success",
  "message": "Incident status updated",
  "warnings": [],
  "data": {
    "incident_id": 1,
    "title": "Suspicious email",
    "description": "Investigate a reported phishing message",
    "category": "Phishing",
    "severity": "High",
    "reporter_id": 3,
    "asset_id": 1,
    "assigned_analyst_id": 2,
    "status": "Mitigated",
    "created_at": "2026-10-20T20:19:50.635848Z",
    "resolved_at": null
  }
}
```

## Jad Moharam 13 PUT /incidents/1/status
HTTP 200 at 2026-10-20T20:19:51.437751+00:00

Request
```json
{
  "status": "Resolved"
}
```

Response
```json
{
  "status": "success",
  "message": "Incident status updated",
  "warnings": [],
  "data": {
    "incident_id": 1,
    "title": "Suspicious email",
    "description": "Investigate a reported phishing message",
    "category": "Phishing",
    "severity": "High",
    "reporter_id": 3,
    "asset_id": 1,
    "assigned_analyst_id": 2,
    "status": "Resolved",
    "created_at": "2026-10-20T20:19:50.635848Z",
    "resolved_at": "2026-10-20T20:19:51.415751Z"
  }
}
```

## Jad Moharam 14 PUT /incidents/1/status
HTTP 200 at 2026-10-20T20:19:51.490293+00:00

Request
```json
{
  "status": "Closed"
}
```

Response
```json
{
  "status": "success",
  "message": "Incident status updated",
  "warnings": [],
  "data": {
    "incident_id": 1,
    "title": "Suspicious email",
    "description": "Investigate a reported phishing message",
    "category": "Phishing",
    "severity": "High",
    "reporter_id": 3,
    "asset_id": 1,
    "assigned_analyst_id": 2,
    "status": "Closed",
    "created_at": "2026-10-20T20:19:50.635848Z",
    "resolved_at": "2026-10-20T20:19:51.415751Z"
  }
}
```

## Jad Moharam 15 POST /incidents/1/notes
HTTP 201 at 2026-10-20T20:19:51.645314+00:00

Request
```json
{
  "content": "Email headers preserved; sender investigated."
}
```

Response
```json
{
  "status": "success",
  "message": "Investigation note added",
  "warnings": [],
  "data": {
    "note_id": 1,
    "incident_id": 1,
    "analyst_id": 2,
    "content": "Email headers preserved; sender investigated.",
    "created_at": "2026-10-20T20:19:51.625315Z"
  }
}
```

## Jad Moharam 16 GET /incidents/1
HTTP 200 at 2026-10-20T20:19:51.838770+00:00

Request
```json
null
```

Response
```json
{
  "status": "success",
  "data": {
    "incident_id": 1,
    "title": "Suspicious email",
    "description": "Investigate a reported phishing message",
    "category": "Phishing",
    "severity": "High",
    "reporter_id": 3,
    "asset_id": 1,
    "assigned_analyst_id": 2,
    "status": "Closed",
    "created_at": "2026-10-20T20:19:50.635848Z",
    "resolved_at": "2026-10-20T20:19:51.415751Z",
    "notes": [
      {
        "note_id": 1,
        "incident_id": 1,
        "analyst_id": 2,
        "content": "Email headers preserved; sender investigated.",
        "created_at": "2026-10-20T20:19:51.625315Z"
      }
    ]
  }
}
```

## Jad Moharam 17 POST /playbooks
HTTP 201 at 2026-10-20T20:19:51.887796+00:00

Request
```json
{
  "name": "Phishing response 1792527592",
  "description": "Investigate and isolate affected systems",
  "incident_category": "Phishing",
  "severity": "High"
}
```

Response
```json
{
  "status": "success",
  "message": "Playbook created",
  "warnings": [],
  "data": {
    "playbook_id": 1,
    "name": "Phishing response 1792527592",
    "description": "Investigate and isolate affected systems",
    "incident_category": "Phishing",
    "severity": "High",
    "created_by": 1,
    "created_at": "2026-10-20T20:19:51.866775Z"
  }
}
```

## Jad Moharam 18 GET /playbooks
HTTP 200 at 2026-10-20T20:19:51.915797+00:00

Request
```json
null
```

Response
```json
{
  "status": "success",
  "count": 1,
  "data": [
    {
      "playbook_id": 1,
      "name": "Phishing response 1792527592",
      "description": "Investigate and isolate affected systems",
      "incident_category": "Phishing",
      "severity": "High",
      "created_by": 1,
      "created_at": "2026-10-20T20:19:51.866775Z"
    }
  ]
}
```

## Jad Moharam 19 GET /playbooks/1
HTTP 200 at 2026-10-20T20:19:51.944796+00:00

Request
```json
null
```

Response
```json
{
  "status": "success",
  "data": {
    "playbook_id": 1,
    "name": "Phishing response 1792527592",
    "description": "Investigate and isolate affected systems",
    "incident_category": "Phishing",
    "severity": "High",
    "created_by": 1,
    "created_at": "2026-10-20T20:19:51.866775Z",
    "actions": [],
    "progress": {
      "total": 0,
      "completed": 0
    }
  }
}
```

## Jad Moharam 20 POST /playbooks/1/actions
HTTP 201 at 2026-10-20T20:19:52.051640+00:00

Request
```json
{
  "description": "Investigate malicious email",
  "step_number": 1,
  "assigned_user_id": 2
}
```

Response
```json
{
  "status": "success",
  "message": "Response action added",
  "warnings": [],
  "data": {
    "action_id": 1,
    "playbook_id": 1,
    "description": "Investigate malicious email",
    "step_number": 1,
    "status": "Pending",
    "assigned_user_id": 2,
    "completed_at": null
  }
}
```

## Jad Moharam 21 PUT /actions/1/status
HTTP 200 at 2026-10-20T20:19:52.274308+00:00

Request
```json
{
  "status": "In Progress"
}
```

Response
```json
{
  "status": "success",
  "message": "Response action updated",
  "warnings": [],
  "data": {
    "action_id": 1,
    "playbook_id": 1,
    "description": "Investigate malicious email",
    "step_number": 1,
    "status": "In Progress",
    "assigned_user_id": 2,
    "completed_at": null
  }
}
```

## Jad Moharam 22 PUT /actions/1/status
HTTP 200 at 2026-10-20T20:19:52.382668+00:00

Request
```json
{
  "status": "Completed"
}
```

Response
```json
{
  "status": "success",
  "message": "Response action updated",
  "warnings": [],
  "data": {
    "action_id": 1,
    "playbook_id": 1,
    "description": "Investigate malicious email",
    "step_number": 1,
    "status": "Completed",
    "assigned_user_id": 2,
    "completed_at": "2026-10-20T20:19:52.364661Z"
  }
}
```

## Jad Moharam 23 GET /incidents
HTTP 401 at 2026-10-20T20:19:52.468677+00:00

Request
```json
null
```

Response
```json
{
  "status": "error",
  "message": "Missing authentication token. Send the header 'Authorization: Bearer <token>'"
}
```

## Jad Moharam 24 GET /incidents
HTTP 403 at 2026-10-20T20:19:52.495381+00:00

Request
```json
null
```

Response
```json
{
  "status": "error",
  "message": "User does not have permission to perform this operation"
}
```

## Jad Moharam 25 GET /incidents/1
HTTP 403 at 2026-10-20T20:19:52.527381+00:00

Request
```json
null
```

Response
```json
{
  "status": "error",
  "message": "Users may access only their own incident reports"
}
```

## Jad Moharam 26 GET /incidents/999999
HTTP 404 at 2026-10-20T20:19:52.556382+00:00

Request
```json
null
```

Response
```json
{
  "status": "error",
  "message": "Incident not found"
}
```

## Jad Moharam 27 POST /incidents
HTTP 400 at 2026-10-20T20:19:52.704726+00:00

Request
```json
{
  "title": "X",
  "description": "X",
  "category": "Malware",
  "severity": "Extreme",
  "asset_id": 1
}
```

Response
```json
{
  "status": "error",
  "message": "severity must be one of: Low, Medium, High, Critical"
}
```

## Jad Moharam 28 PUT /incidents/1/assign
HTTP 403 at 2026-10-20T20:19:52.849677+00:00

Request
```json
{
  "analyst_id": 2
}
```

Response
```json
{
  "status": "error",
  "message": "User does not have permission to perform this operation"
}
```

## Jad Moharam 29 PUT /incidents/1/assign
HTTP 400 at 2026-10-20T20:19:52.919695+00:00

Request
```json
{
  "analyst_id": 3
}
```

Response
```json
{
  "status": "error",
  "message": "Assigned user must have the Security Analyst role"
}
```

## Jad Moharam 30 PUT /incidents/1/status
HTTP 400 at 2026-10-20T20:19:52.944696+00:00

Request
```json
{
  "status": "Open"
}
```

Response
```json
{
  "status": "error",
  "message": "Invalid incident status transition"
}
```

## Jad Moharam 31 POST /incidents/1/notes
HTTP 400 at 2026-10-20T20:19:52.967699+00:00

Request
```json
{
  "content": " "
}
```

Response
```json
{
  "status": "error",
  "message": "content must be nonempty text of at most 5000 characters"
}
```

## Jad Moharam 32 GET /notifications/1
HTTP 403 at 2026-10-20T20:19:53.040710+00:00

Request
```json
null
```

Response
```json
{
  "status": "error",
  "message": "Users may access only their own notifications"
}
```

## Jad Moharam 33 PUT /notifications/1/read
HTTP 403 at 2026-10-20T20:19:53.098255+00:00

Request
```json
null
```

Response
```json
{
  "status": "error",
  "message": "User does not have permission to perform this operation"
}
```

## Jad Moharam 34 POST /notifications
HTTP 400 at 2026-10-20T20:19:53.126253+00:00

Request
```json
{
  "user_id": 3,
  "title": "X",
  "message": "X",
  "type": "Email",
  "severity": "Low"
}
```

Response
```json
{
  "status": "error",
  "message": "type must be one of: Incident Assignment, Security Alert, System Notification, Threat Alert, Vulnerability Alert"
}
```

## Jad Moharam 35 POST /notifications
HTTP 400 at 2026-10-20T20:19:53.279789+00:00

Request
```json
{}
```

Response
```json
{
  "status": "error",
  "message": "A nonempty JSON object is required"
}
```

## Jad Moharam 36 GET /notifications/999999
HTTP 404 at 2026-10-20T20:19:53.482844+00:00

Request
```json
null
```

Response
```json
{
  "status": "error",
  "message": "Notification not found"
}
```

## Jad Moharam 37 DELETE /notifications/1
HTTP 403 at 2026-10-20T20:19:53.514330+00:00

Request
```json
null
```

Response
```json
{
  "status": "error",
  "message": "User does not have permission to perform this operation"
}
```

## Jad Moharam 38 GET /notifications/search?user_id=3
HTTP 403 at 2026-10-20T20:19:53.559334+00:00

Request
```json
null
```

Response
```json
{
  "status": "error",
  "message": "Users may access only their own notifications"
}
```

## Jad Moharam 39 GET /notifications/search?status=Maybe
HTTP 400 at 2026-10-20T20:19:53.807501+00:00

Request
```json
null
```

Response
```json
{
  "status": "error",
  "message": "status must be one of: Unread, Read"
}
```

## Jad Moharam 40 GET /playbooks
HTTP 403 at 2026-10-20T20:19:53.942527+00:00

Request
```json
null
```

Response
```json
{
  "status": "error",
  "message": "User does not have permission to perform this operation"
}
```

## Jad Moharam 41 GET /playbooks/999999
HTTP 404 at 2026-10-20T20:19:54.006549+00:00

Request
```json
null
```

Response
```json
{
  "status": "error",
  "message": "Playbook not found"
}
```

## Jad Moharam 42 POST /playbooks/1/actions
HTTP 409 at 2026-10-20T20:19:54.043551+00:00

Request
```json
{
  "description": "Duplicate",
  "step_number": 1
}
```

Response
```json
{
  "status": "error",
  "message": "Duplicate step number"
}
```

## Jad Moharam 43 POST /playbooks/1/actions
HTTP 400 at 2026-10-20T20:19:54.071555+00:00

Request
```json
{
  "description": "Gap",
  "step_number": 3
}
```

Response
```json
{
  "status": "error",
  "message": "Next step_number must be 2"
}
```

## Jad Moharam 44 PUT /actions/1/status
HTTP 400 at 2026-10-20T20:19:54.098137+00:00

Request
```json
{
  "status": "Done"
}
```

Response
```json
{
  "status": "error",
  "message": "status must be one of: Pending, In Progress, Completed"
}
```

## Jad Moharam 45 PUT /actions/999999/status
HTTP 404 at 2026-10-20T20:19:54.240157+00:00

Request
```json
{
  "status": "In Progress"
}
```

Response
```json
{
  "status": "error",
  "message": "Response action not found"
}
```

## Jad Moharam 46 DELETE /playbooks/1
HTTP 403 at 2026-10-20T20:19:54.350184+00:00

Request
```json
null
```

Response
```json
{
  "status": "error",
  "message": "User does not have permission to perform this operation"
}
```

## Jad Moharam 47 DELETE /notifications/1
HTTP 200 at 2026-10-20T20:19:54.444206+00:00

Request
```json
null
```

Response
```json
{
  "status": "success",
  "message": "Notification deleted",
  "warnings": [],
  "data": {
    "notification_id": 1
  }
}
```

## Jad Moharam 48 DELETE /playbooks/1
HTTP 200 at 2026-10-20T20:19:54.491177+00:00

Request
```json
null
```

Response
```json
{
  "status": "success",
  "message": "Playbook deleted",
  "warnings": [],
  "data": {
    "playbook_id": 1
  }
}
```

## Omar Tabsh 1 POST /threats
HTTP 201 at 2026-10-20T20:32:11.750562+00:00

Request
```json
{
  "threat_type": "Domain",
  "threat_value": "sprint-evidence.example",
  "description": "Development evidence indicator",
  "severity": "High",
  "source": "Team local test"
}
```

Response
```json
{
  "status": "success",
  "message": "Threat indicator added successfully",
  "data": {
    "threat_id": 1,
    "threat_type": "Domain",
    "threat_value": "sprint-evidence.example",
    "description": "Development evidence indicator",
    "severity": "High",
    "source": "Team local test",
    "date_added": "2026-10-20 20:32:11",
    "last_updated": null
  }
}
```

## Omar Tabsh 2 GET /threats
HTTP 200 at 2026-10-20T20:32:11.753561+00:00

Request
```json
null
```

Response
```json
{
  "status": "success",
  "count": 1,
  "data": [
    {
      "threat_id": 1,
      "threat_type": "Domain",
      "threat_value": "sprint-evidence.example",
      "description": "Development evidence indicator",
      "severity": "High",
      "source": "Team local test",
      "date_added": "2026-10-20 20:32:11",
      "last_updated": null
    }
  ]
}
```

## Omar Tabsh 3 GET /threats/1
HTTP 200 at 2026-10-20T20:32:11.756561+00:00

Request
```json
null
```

Response
```json
{
  "status": "success",
  "data": {
    "threat_id": 1,
    "threat_type": "Domain",
    "threat_value": "sprint-evidence.example",
    "description": "Development evidence indicator",
    "severity": "High",
    "source": "Team local test",
    "date_added": "2026-10-20 20:32:11",
    "last_updated": null
  }
}
```

## Omar Tabsh 4 GET /threats/search?severity=High
HTTP 200 at 2026-10-20T20:32:11.759328+00:00

Request
```json
null
```

Response
```json
{
  "status": "success",
  "message": "1 threat indicator(s) matched the search",
  "count": 1,
  "filters": {
    "severity": "High"
  },
  "data": [
    {
      "threat_id": 1,
      "threat_type": "Domain",
      "threat_value": "sprint-evidence.example",
      "description": "Development evidence indicator",
      "severity": "High",
      "source": "Team local test",
      "date_added": "2026-10-20 20:32:11",
      "last_updated": null
    }
  ]
}
```

## Omar Tabsh 5 PUT /threats/1
HTTP 200 at 2026-10-20T20:32:11.771008+00:00

Request
```json
{
  "severity": "Critical",
  "description": "Confirmed development indicator"
}
```

Response
```json
{
  "status": "success",
  "message": "Threat information updated successfully",
  "previous_values": {
    "description": "Development evidence indicator",
    "severity": "High"
  },
  "data": {
    "threat_id": 1,
    "threat_type": "Domain",
    "threat_value": "sprint-evidence.example",
    "description": "Confirmed development indicator",
    "severity": "Critical",
    "source": "Team local test",
    "date_added": "2026-10-20 20:32:11",
    "last_updated": "2026-10-20 20:32:11"
  }
}
```

## Omar Tabsh 6 POST /logs
HTTP 201 at 2026-10-20T20:32:11.777010+00:00

Request
```json
{
  "user_id": 1,
  "action": "TEAM_EVIDENCE",
  "description": "Common report evidence run",
  "severity": "Information",
  "related_service": "Users"
}
```

Response
```json
{
  "status": "success",
  "message": "Log record created successfully",
  "data": {
    "log_id": 30,
    "user_id": 1,
    "action": "TEAM_EVIDENCE",
    "description": "Common report evidence run",
    "timestamp": "2026-10-20 20:32:11",
    "severity": "Information",
    "related_service": "Users"
  }
}
```

## Omar Tabsh 7 GET /logs
HTTP 200 at 2026-10-20T20:32:11.780008+00:00

Request
```json
null
```

Response
```json
{
  "status": "success",
  "count": 30,
  "data": [
    {
      "log_id": 30,
      "user_id": 1,
      "action": "TEAM_EVIDENCE",
      "description": "Common report evidence run",
      "timestamp": "2026-10-20 20:32:11",
      "severity": "Information",
      "related_service": "Users"
    },
    {
      "log_id": 29,
      "user_id": 1,
      "action": "THREAT_UPDATED",
      "description": "Threat #1 (Domain 'sprint-evidence.example') updated: description: 'Development evidence indicator' -> 'Confirmed development indicator'; severity: 'High' -> 'Critical'",
      "timestamp": "2026-10-20 20:32:11",
      "severity": "Information",
      "related_service": "Threat Intelligence"
    },
    {
      "log_id": 28,
      "user_id": 1,
      "action": "THREAT_CREATED",
      "description": "Threat #1 added: Domain 'sprint-evidence.example' (severity High, source Team local test)",
      "timestamp": "2026-10-20 20:32:11",
      "severity": "Information",
      "related_service": "Threat Intelligence"
    },
    {
      "log_id": 27,
      "user_id": 1,
      "action": "PLAYBOOK_DELETED",
      "description": "Playbook 1 deleted; action history retained",
      "timestamp": "2026-10-20 20:19:54",
      "severity": "Information",
      "related_service": "Playbooks"
    },
    {
      "log_id": 26,
      "user_id": 1,
      "action": "NOTIFICATION_DELETED",
      "description": "Notification 1 deleted",
      "timestamp": "2026-10-20 20:19:54",
      "severity": "Information",
      "related_service": "Notifications"
    },
    {
      "log_id": 25,
      "user_id": 2,
      "action": "UNAUTHORIZED_ACCESS",
      "description": "User 'analyst_dev' (id 2, role Security Analyst) was denied access to DELETE /playbooks/1",
      "timestamp": "2026-10-20 20:19:54",
      "severity": "Warning",
      "related_service": "Playbooks"
    },
    {
      "log_id": 24,
      "user_id": 3,
      "action": "UNAUTHORIZED_ACCESS",
      "description": "User 'user_dev' (id 3, role Regular Employee/User) was denied access to GET /playbooks",
      "timestamp": "2026-10-20 20:19:53",
      "severity": "Warning",
      "related_service": "Playbooks"
    },
    {
      "log_id": 23,
      "user_id": 2,
      "action": "UNAUTHORIZED_ACCESS",
      "description": "Users may access only their own notifications",
      "timestamp": "2026-10-20 20:19:53",
      "severity": "Warning",
      "related_service": "Notifications"
    },
    {
      "log_id": 22,
      "user_id": 3,
      "action": "UNAUTHORIZED_ACCESS",
      "description": "User 'user_dev' (id 3, role Regular Employee/User) was denied access to DELETE /notifications/1",
      "timestamp": "2026-10-20 20:19:53",
      "severity": "Warning",
      "related_service": "Notifications"
    },
    {
      "log_id": 21,
      "user_id": 4,
      "action": "UNAUTHORIZED_ACCESS",
      "description": "User 'auditor_dev' (id 4, role Auditor) was denied access to PUT /notifications/1/read",
      "timestamp": "2026-10-20 20:19:53",
      "severity": "Warning",
      "related_service": "Notifications"
    },
    {
      "log_id": 20,
      "user_id": 6,
      "action": "UNAUTHORIZED_ACCESS",
      "description": "Users may access only their own notifications",
      "timestamp": "2026-10-20 20:19:53",
      "severity": "Warning",
      "related_service": "Notifications"
    },
    {
      "log_id": 19,
      "user_id": 3,
      "action": "UNAUTHORIZED_ACCESS",
      "description": "User 'user_dev' (id 3, role Regular Employee/User) was denied access to PUT /incidents/1/assign",
      "timestamp": "2026-10-20 20:19:52",
      "severity": "Warning",
      "related_service": "Incidents"
    },
    {
      "log_id": 18,
      "user_id": 6,
      "action": "UNAUTHORIZED_ACCESS",
      "description": "Users may access only their own incident reports",
      "timestamp": "2026-10-20 20:19:52",
      "severity": "Warning",
      "related_service": "Incidents"
    },
    {
      "log_id": 17,
      "user_id": 2,
      "action": "UNAUTHORIZED_ACCESS",
      "description": "User 'analyst_dev' (id 2, role Security Analyst) was denied access to GET /incidents",
      "timestamp": "2026-10-20 20:19:52",
      "severity": "Warning",
      "related_service": "Incidents"
    },
    {
      "log_id": 16,
      "user_id": null,
      "action": "UNAUTHORIZED_ACCESS",
      "description": "Rejected unauthenticated request to GET /incidents: Missing authentication token. Send the header 'Authorization: Bearer <token>'",
      "timestamp": "2026-10-20 20:19:52",
      "severity": "Warning",
      "related_service": "Incidents"
    },
    {
      "log_id": 15,
      "user_id": 2,
      "action": "RESPONSE_ACTION_UPDATED",
      "description": "Action 1: In Progress -> Completed",
      "timestamp": "2026-10-20 20:19:52",
      "severity": "Information",
      "related_service": "Playbooks"
    },
    {
      "log_id": 14,
      "user_id": 2,
      "action": "RESPONSE_ACTION_UPDATED",
      "description": "Action 1: Pending -> In Progress",
      "timestamp": "2026-10-20 20:19:52",
      "severity": "Information",
      "related_service": "Playbooks"
    },
    {
      "log_id": 13,
      "user_id": 2,
      "action": "RESPONSE_ACTION_ADDED",
      "description": "Action 1 added to playbook 1",
      "timestamp": "2026-10-20 20:19:52",
      "severity": "Information",
      "related_service": "Playbooks"
    },
    {
      "log_id": 12,
      "user_id": 1,
      "action": "PLAYBOOK_CREATED",
      "description": "Playbook 1 created",
      "timestamp": "2026-10-20 20:19:51",
      "severity": "Information",
      "related_service": "Playbooks"
    },
    {
      "log_id": 11,
      "user_id": 2,
      "action": "INCIDENT_NOTE_ADDED",
      "description": "Note 1 added to incident 1",
      "timestamp": "2026-10-20 20:19:51",
      "severity": "Information",
      "related_service": "Incidents"
    },
    {
      "log_id": 10,
      "user_id": 2,
      "action": "INCIDENT_STATUS_CHANGED",
      "description": "Incident 1: Resolved -> Closed",
      "timestamp": "2026-10-20 20:19:51",
      "severity": "Information",
      "related_service": "Incidents"
    },
    {
      "log_id": 9,
      "user_id": 2,
      "action": "INCIDENT_STATUS_CHANGED",
      "description": "Incident 1: Mitigated -> Resolved",
      "timestamp": "2026-10-20 20:19:51",
      "severity": "Information",
      "related_service": "Incidents"
    },
    {
      "log_id": 8,
      "user_id": 2,
      "action": "INCIDENT_STATUS_CHANGED",
      "description": "Incident 1: Under Investigation -> Mitigated",
      "timestamp": "2026-10-20 20:19:51",
      "severity": "Information",
      "related_service": "Incidents"
    },
    {
      "log_id": 7,
      "user_id": 2,
      "action": "INCIDENT_STATUS_CHANGED",
      "description": "Incident 1: Open -> Under Investigation",
      "timestamp": "2026-10-20 20:19:51",
      "severity": "Information",
      "related_service": "Incidents"
    },
    {
      "log_id": 6,
      "user_id": null,
      "action": "NOTIFICATION_CREATED",
      "description": "Notification 2 created for user 2",
      "timestamp": "2026-10-20 20:19:50",
      "severity": "Information",
      "related_service": "Notifications"
    },
    {
      "log_id": 5,
      "user_id": 1,
      "action": "INCIDENT_ASSIGNED",
      "description": "Incident 1 assigned to analyst 2",
      "timestamp": "2026-10-20 20:19:50",
      "severity": "Information",
      "related_service": "Incidents"
    },
    {
      "log_id": 4,
      "user_id": 1,
      "action": "INCIDENT_ASSIGNMENT_AUTHORIZED",
      "description": "Assignment authorized: incident 1 to analyst 2",
      "timestamp": "2026-10-20 20:19:50",
      "severity": "Information",
      "related_service": "Incidents"
    },
    {
      "log_id": 3,
      "user_id": 1,
      "action": "INCIDENT_CREATED",
      "description": "Incident 1 created",
      "timestamp": "2026-10-20 20:19:50",
      "severity": "Information",
      "related_service": "Incidents"
    },
    {
      "log_id": 2,
      "user_id": 3,
      "action": "NOTIFICATION_READ",
      "description": "Notification 1 marked read",
      "timestamp": "2026-10-20 20:19:50",
      "severity": "Information",
      "related_service": "Notifications"
    },
    {
      "log_id": 1,
      "user_id": 1,
      "action": "NOTIFICATION_CREATED",
      "description": "Notification 1 created for user 3",
      "timestamp": "2026-10-20 20:19:50",
      "severity": "Information",
      "related_service": "Notifications"
    }
  ]
}
```

## Omar Tabsh 8 GET /logs/30
HTTP 200 at 2026-10-20T20:32:11.783008+00:00

Request
```json
null
```

Response
```json
{
  "status": "success",
  "data": {
    "log_id": 30,
    "user_id": 1,
    "action": "TEAM_EVIDENCE",
    "description": "Common report evidence run",
    "timestamp": "2026-10-20 20:32:11",
    "severity": "Information",
    "related_service": "Users"
  }
}
```

## Omar Tabsh 9 GET /logs/search?action=TEAM_EVIDENCE
HTTP 200 at 2026-10-20T20:32:11.786007+00:00

Request
```json
null
```

Response
```json
{
  "status": "success",
  "message": "1 log record(s) matched the search",
  "count": 1,
  "filters": {
    "action": "TEAM_EVIDENCE"
  },
  "data": [
    {
      "log_id": 30,
      "user_id": 1,
      "action": "TEAM_EVIDENCE",
      "description": "Common report evidence run",
      "timestamp": "2026-10-20 20:32:11",
      "severity": "Information",
      "related_service": "Users"
    }
  ]
}
```

## Omar Tabsh 10 GET /logs/user/1
HTTP 200 at 2026-10-20T20:32:11.788008+00:00

Request
```json
null
```

Response
```json
{
  "status": "success",
  "message": "10 log record(s) found for user 1",
  "count": 10,
  "user_id": 1,
  "data": [
    {
      "log_id": 30,
      "user_id": 1,
      "action": "TEAM_EVIDENCE",
      "description": "Common report evidence run",
      "timestamp": "2026-10-20 20:32:11",
      "severity": "Information",
      "related_service": "Users"
    },
    {
      "log_id": 29,
      "user_id": 1,
      "action": "THREAT_UPDATED",
      "description": "Threat #1 (Domain 'sprint-evidence.example') updated: description: 'Development evidence indicator' -> 'Confirmed development indicator'; severity: 'High' -> 'Critical'",
      "timestamp": "2026-10-20 20:32:11",
      "severity": "Information",
      "related_service": "Threat Intelligence"
    },
    {
      "log_id": 28,
      "user_id": 1,
      "action": "THREAT_CREATED",
      "description": "Threat #1 added: Domain 'sprint-evidence.example' (severity High, source Team local test)",
      "timestamp": "2026-10-20 20:32:11",
      "severity": "Information",
      "related_service": "Threat Intelligence"
    },
    {
      "log_id": 27,
      "user_id": 1,
      "action": "PLAYBOOK_DELETED",
      "description": "Playbook 1 deleted; action history retained",
      "timestamp": "2026-10-20 20:19:54",
      "severity": "Information",
      "related_service": "Playbooks"
    },
    {
      "log_id": 26,
      "user_id": 1,
      "action": "NOTIFICATION_DELETED",
      "description": "Notification 1 deleted",
      "timestamp": "2026-10-20 20:19:54",
      "severity": "Information",
      "related_service": "Notifications"
    },
    {
      "log_id": 12,
      "user_id": 1,
      "action": "PLAYBOOK_CREATED",
      "description": "Playbook 1 created",
      "timestamp": "2026-10-20 20:19:51",
      "severity": "Information",
      "related_service": "Playbooks"
    },
    {
      "log_id": 5,
      "user_id": 1,
      "action": "INCIDENT_ASSIGNED",
      "description": "Incident 1 assigned to analyst 2",
      "timestamp": "2026-10-20 20:19:50",
      "severity": "Information",
      "related_service": "Incidents"
    },
    {
      "log_id": 4,
      "user_id": 1,
      "action": "INCIDENT_ASSIGNMENT_AUTHORIZED",
      "description": "Assignment authorized: incident 1 to analyst 2",
      "timestamp": "2026-10-20 20:19:50",
      "severity": "Information",
      "related_service": "Incidents"
    },
    {
      "log_id": 3,
      "user_id": 1,
      "action": "INCIDENT_CREATED",
      "description": "Incident 1 created",
      "timestamp": "2026-10-20 20:19:50",
      "severity": "Information",
      "related_service": "Incidents"
    },
    {
      "log_id": 1,
      "user_id": 1,
      "action": "NOTIFICATION_CREATED",
      "description": "Notification 1 created for user 3",
      "timestamp": "2026-10-20 20:19:50",
      "severity": "Information",
      "related_service": "Notifications"
    }
  ]
}
```

## Omar Tabsh 11 GET /reports/summary
HTTP 503 at 2026-10-20T20:32:13.841525+00:00

Request
```json
null
```

Response
```json
{
  "status": "error",
  "message": "Could not generate the Security Summary Report: The Users and Identity Management service is not reachable at http://127.0.0.1:5191/users. Make sure it is running",
  "errors": {
    "source": "Users and Identity Management"
  }
}
```

## Omar Tabsh 12 GET /reports/incidents
HTTP 200 at 2026-10-20T20:32:13.847524+00:00

Request
```json
null
```

Response
```json
{
  "status": "success",
  "message": "Incident Report generated successfully",
  "data": {
    "total_incidents": 1,
    "incidents_by_severity": {
      "Low": 0,
      "Medium": 0,
      "High": 1,
      "Critical": 0
    },
    "incidents_by_status": {
      "Open": 0,
      "Under Investigation": 0,
      "Mitigated": 0,
      "Resolved": 0,
      "Closed": 1
    },
    "generated_at": "2026-10-20 20:32:13 UTC",
    "data_sources": [
      "Incident Management service: GET http://127.0.0.1:5103/incidents"
    ]
  }
}
```

## Omar Tabsh 13 GET /reports/assets
HTTP 503 at 2026-10-20T20:32:15.870644+00:00

Request
```json
null
```

Response
```json
{
  "status": "error",
  "message": "Could not generate the Asset Report: The Asset Management service is not reachable at http://127.0.0.1:5192/assets. Make sure it is running",
  "errors": {
    "source": "Asset Management"
  }
}
```

## Omar Tabsh 14 GET /reports/threats
HTTP 200 at 2026-10-20T20:32:15.875644+00:00

Request
```json
null
```

Response
```json
{
  "status": "success",
  "message": "Threat Report generated successfully",
  "data": {
    "total_threats": 1,
    "threats_by_severity": {
      "Low": 0,
      "Medium": 0,
      "High": 0,
      "Critical": 1
    },
    "threats_by_type": {
      "IP Address": 0,
      "Domain": 1,
      "File Hash": 0,
      "Malware Signature": 0,
      "Other": 0
    },
    "recently_added_threats": [
      {
        "threat_id": 1,
        "threat_type": "Domain",
        "threat_value": "sprint-evidence.example",
        "severity": "Critical",
        "source": "Team local test",
        "date_added": "2026-10-20 20:32:11"
      }
    ],
    "generated_at": "2026-10-20 20:32:15 UTC",
    "data_sources": [
      "Threat Intelligence service: GET http://127.0.0.1:5104/threats"
    ]
  }
}
```

## Omar Tabsh 15 GET /reports/vulnerabilities
HTTP 503 at 2026-10-20T20:32:17.922599+00:00

Request
```json
null
```

Response
```json
{
  "status": "error",
  "message": "Could not generate the Vulnerability Report: The Vulnerability Management service is not reachable at http://127.0.0.1:5197/vulnerabilities. Make sure it is running",
  "errors": {
    "source": "Vulnerability Management"
  }
}
```

## Omar Tabsh 16 GET /reports/activity
HTTP 200 at 2026-10-20T20:32:17.930108+00:00

Request
```json
null
```

Response
```json
{
  "status": "success",
  "message": "Activity Report generated successfully",
  "data": {
    "total_user_activities": 30,
    "login_attempts": 0,
    "successful_logins": 0,
    "failed_login_attempts": 0,
    "unauthorized_access_attempts": 10,
    "most_performed_actions": [
      {
        "action": "UNAUTHORIZED_ACCESS",
        "count": 10
      },
      {
        "action": "INCIDENT_STATUS_CHANGED",
        "count": 4
      },
      {
        "action": "NOTIFICATION_CREATED",
        "count": 2
      },
      {
        "action": "RESPONSE_ACTION_UPDATED",
        "count": 2
      },
      {
        "action": "INCIDENT_ASSIGNED",
        "count": 1
      }
    ],
    "activities_by_severity": {
      "Information": 20,
      "Warning": 10,
      "Error": 0,
      "Critical": 0
    },
    "generated_at": "2026-10-20 20:32:17 UTC",
    "data_sources": [
      "Security Audit Logging service: GET http://127.0.0.1:5105/logs"
    ]
  }
}
```

## Omar Tabsh 17 POST /threats
HTTP 403 at 2026-10-20T20:32:17.939887+00:00

Request
```json
{}
```

Response
```json
{
  "status": "error",
  "message": "User does not have permission to perform this operation"
}
```

## Omar Tabsh 18 POST /threats
HTTP 400 at 2026-10-20T20:32:17.943883+00:00

Request
```json
{
  "threat_type": "Domain",
  "threat_value": "https://invalid/path",
  "description": "Invalid",
  "severity": "High",
  "source": "Local test"
}
```

Response
```json
{
  "status": "error",
  "message": "Invalid threat indicator",
  "errors": {
    "threat_value": "'https://invalid/path' is not a valid domain name (expected something like malicious-site.com, without http:// or a path)"
  }
}
```

## Omar Tabsh 19 DELETE /logs/30
HTTP 200 at 2026-10-20T20:32:17.954884+00:00

Request
```json
null
```

Response
```json
{
  "status": "success",
  "message": "Log record 30 deleted successfully",
  "data": {
    "log_id": 30,
    "user_id": 1,
    "action": "TEAM_EVIDENCE",
    "description": "Common report evidence run",
    "timestamp": "2026-10-20 20:32:11",
    "severity": "Information",
    "related_service": "Users"
  }
}
```

## Omar Tabsh 20 DELETE /threats/1
HTTP 200 at 2026-10-20T20:32:17.966884+00:00

Request
```json
null
```

Response
```json
{
  "status": "success",
  "message": "Threat indicator 1 deleted successfully",
  "data": {
    "threat_id": 1,
    "threat_type": "Domain",
    "threat_value": "sprint-evidence.example",
    "description": "Confirmed development indicator",
    "severity": "Critical",
    "source": "Team local test",
    "date_added": "2026-10-20 20:32:11",
    "last_updated": "2026-10-20 20:32:11"
  }
}
```