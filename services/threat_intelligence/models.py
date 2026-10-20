# Service 4 - Threat Intelligence: threat data rules and input validation
# Omar Tabsh - 202400798

import ipaddress
import re

IP_ADDRESS = "IP Address"
DOMAIN = "Domain"
FILE_HASH = "File Hash"
MALWARE_SIGNATURE = "Malware Signature"
OTHER = "Other"
THREAT_TYPES = (IP_ADDRESS, DOMAIN, FILE_HASH, MALWARE_SIGNATURE, OTHER)

SEVERITIES = ("Low", "Medium", "High", "Critical")

# Extra spellings accepted for convenience; they are stored using the official name
_TYPE_ALIASES = {"ip": IP_ADDRESS, "hash": FILE_HASH, "other indicator": OTHER,
                 "other indicators": OTHER}

# MD5 (32), SHA-1 (40), SHA-256 (64) and SHA-512 (128) hexadecimal digests
_HASH_LENGTHS = {32: "MD5", 40: "SHA-1", 64: "SHA-256", 128: "SHA-512"}
_HEX_RE = re.compile(r"^[0-9a-f]+$")
# Labels of 1-63 letters/digits/hyphens (not starting or ending with a hyphen), then a TLD
_DOMAIN_RE = re.compile(r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$")

CREATE_FIELDS = ("threat_type", "threat_value", "description", "severity", "source")
UPDATE_FIELDS = ("description", "severity", "source")

MAX_DESCRIPTION = 1000
MAX_SOURCE = 100
MAX_VALUE = 255


class ValidationError(Exception):
    """Raised with a dict of {field: problem} when input is invalid."""

    def __init__(self, errors):
        super().__init__("Validation failed")
        self.errors = errors


class ThreatValidator:
    """Checks and normalises threat input before it reaches the database."""

    @staticmethod
    def normalize_type(raw):
        if not isinstance(raw, str) or not raw.strip():
            raise ValueError("threat_type is required")
        key = " ".join(raw.replace("_", " ").split()).lower()
        for threat_type in THREAT_TYPES:
            if key == threat_type.lower():
                return threat_type
        if key in _TYPE_ALIASES:
            return _TYPE_ALIASES[key]
        raise ValueError(f"threat_type must be one of: {', '.join(THREAT_TYPES)}")

    @staticmethod
    def normalize_severity(raw):
        if not isinstance(raw, str) or not raw.strip():
            raise ValueError("severity is required")
        for severity in SEVERITIES:
            if raw.strip().lower() == severity.lower():
                return severity
        raise ValueError(f"severity must be one of: {', '.join(SEVERITIES)}")

    @staticmethod
    def normalize_value(threat_type, raw):
        """Validate the value for its type and return it in a standard form.

        Domains and hashes are lower-cased so that 'EVIL.com' and 'evil.com'
        are detected as the same indicator.
        """
        if not isinstance(raw, str) or not raw.strip():
            raise ValueError("threat_value is required")
        value = raw.strip()
        if len(value) > MAX_VALUE:
            raise ValueError(f"threat_value must be at most {MAX_VALUE} characters")

        if threat_type == IP_ADDRESS:
            try:
                return str(ipaddress.ip_address(value))
            except ValueError:
                raise ValueError(f"'{value}' is not a valid IPv4 or IPv6 address")

        if threat_type == DOMAIN:
            domain = value.lower().rstrip(".")
            if len(domain) > 253 or not _DOMAIN_RE.match(domain):
                raise ValueError(f"'{value}' is not a valid domain name "
                                 "(expected something like malicious-site.com, without http:// or a path)")
            return domain

        if threat_type == FILE_HASH:
            digest = value.lower()
            if not _HEX_RE.match(digest) or len(digest) not in _HASH_LENGTHS:
                raise ValueError(f"'{value}' is not a valid file hash "
                                 "(expected MD5, SHA-1, SHA-256 or SHA-512 in hexadecimal: 32, 40, 64 or 128 characters)")
            return digest

        if threat_type == MALWARE_SIGNATURE and len(value) < 3:
            raise ValueError("A malware signature must be at least 3 characters long")
        return value

    @staticmethod
    def _text(payload, field, max_length, errors):
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip():
            errors[field] = f"{field} is required and must be a non-empty string"
            return None
        value = value.strip()
        if len(value) > max_length:
            errors[field] = f"{field} must be at most {max_length} characters"
            return None
        return value

    @classmethod
    def _reject_unknown(cls, payload, allowed, errors):
        for field in payload:
            if field not in allowed:
                errors[field] = f"Unknown field. Allowed fields: {', '.join(allowed)}"

    @classmethod
    def validate_new(cls, payload):
        """Validate a POST /threats body and return the cleaned threat."""
        errors = {}
        cls._reject_unknown(payload, CREATE_FIELDS, errors)
        cleaned = {}

        try:
            cleaned["threat_type"] = cls.normalize_type(payload.get("threat_type"))
        except ValueError as exc:
            errors["threat_type"] = str(exc)

        if "threat_type" in cleaned:
            try:
                cleaned["threat_value"] = cls.normalize_value(cleaned["threat_type"],
                                                              payload.get("threat_value"))
            except ValueError as exc:
                errors["threat_value"] = str(exc)
        elif not payload.get("threat_value"):
            errors["threat_value"] = "threat_value is required"

        try:
            cleaned["severity"] = cls.normalize_severity(payload.get("severity"))
        except ValueError as exc:
            errors["severity"] = str(exc)

        cleaned["description"] = cls._text(payload, "description", MAX_DESCRIPTION, errors)
        cleaned["source"] = cls._text(payload, "source", MAX_SOURCE, errors)

        if errors:
            raise ValidationError(errors)
        return cleaned

    @classmethod
    def validate_update(cls, payload):
        """Validate a PUT /threats/{id} body. Only description, severity and source can change."""
        errors = {}
        for field in payload:
            if field in ("threat_type", "threat_value"):
                errors[field] = ("threat_type and threat_value identify the indicator and cannot be "
                                 "changed. Delete it and add a new indicator instead")
            elif field not in UPDATE_FIELDS:
                errors[field] = f"Unknown field. Updatable fields: {', '.join(UPDATE_FIELDS)}"

        cleaned = {}
        if "description" in payload:
            cleaned["description"] = cls._text(payload, "description", MAX_DESCRIPTION, errors)
        if "source" in payload:
            cleaned["source"] = cls._text(payload, "source", MAX_SOURCE, errors)
        if "severity" in payload:
            try:
                cleaned["severity"] = cls.normalize_severity(payload["severity"])
            except ValueError as exc:
                errors["severity"] = str(exc)

        if not errors and not cleaned:
            errors["body"] = f"Provide at least one of: {', '.join(UPDATE_FIELDS)}"
        if errors:
            raise ValidationError(errors)
        return cleaned
