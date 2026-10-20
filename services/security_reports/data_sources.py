# Service 6 - Security Reports: clients that fetch real records from the other services
# Omar Tabsh - 202400798
#
# The Reports service never reads another service's tables. It calls that
# service's "retrieve all" API and forwards the caller's own token. This works
# because the Security Administrator and the Auditor (the only roles allowed to
# generate reports) are also allowed to call every one of these APIs.

import requests

from common import config


class DataSourceError(Exception):
    """A source service could not be reached or returned an unusable answer."""

    def __init__(self, source_name, message, status_code):
        super().__init__(message)
        self.source_name = source_name
        self.status_code = status_code


def extract_records(body):
    """Find the list of records in a response.

    Accepts {"status": "success", "data": [...]} (our agreed format), a plain list,
    or {"data": {"items": [...]}}.
    """
    if isinstance(body, list):
        return body
    if isinstance(body, dict):
        data = body.get("data")
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for value in data.values():
                if isinstance(value, list):
                    return value
        for value in body.values():
            if isinstance(value, list):
                return value
    return None


class ServiceClient:
    def __init__(self, name, base_url, path, timeout=5):
        self.name = name
        self.url = base_url.rstrip("/") + path
        self.timeout = timeout

    def describe(self):
        return f"{self.name} service: GET {self.url}"

    def fetch_all(self, authorization_header):
        try:
            response = requests.get(self.url, headers={"Authorization": authorization_header},
                                    timeout=self.timeout)
        except requests.RequestException:
            raise DataSourceError(self.name, f"The {self.name} service is not reachable at {self.url}. "
                                             "Make sure it is running", 503)

        try:
            body = response.json()
        except ValueError:
            body = None

        if response.status_code != 200:
            detail = body.get("message") if isinstance(body, dict) else response.text[:200]
            raise DataSourceError(self.name, f"The {self.name} service answered HTTP "
                                             f"{response.status_code}: {detail}", 502)

        records = extract_records(body)
        if records is None:
            raise DataSourceError(self.name, f"The {self.name} service returned data in an "
                                             "unexpected format (no list of records found)", 502)
        return [record for record in records if isinstance(record, dict)]


# key -> (display name, service name in config.SERVICE_PORTS, "retrieve all" path)
SOURCES = {
    "users": ("Users and Identity Management", "users", "/users"),
    "assets": ("Asset Management", "assets", "/assets"),
    "incidents": ("Incident Management", "incidents", "/incidents"),
    "threats": ("Threat Intelligence", "threats", "/threats"),
    "vulnerabilities": ("Vulnerability Management", "vulnerabilities", "/vulnerabilities"),
    "logs": ("Security Audit Logging", "logs", "/logs"),
}


def build_clients(url_overrides=None):
    url_overrides = url_overrides or {}
    clients = {}
    for key, (display_name, service, path) in SOURCES.items():
        base_url = url_overrides.get(service) or config.service_url(service)
        clients[key] = ServiceClient(display_name, base_url, path)
    return clients
