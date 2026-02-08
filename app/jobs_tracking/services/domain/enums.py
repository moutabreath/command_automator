"""Job application state enumeration."""
from enum import StrEnum


class JobApplicationState(StrEnum):
    CONNECTION_REQUESTED = "CONNECTION_REQUESTED"
    MESSAGE_SENT = "MESSAGE_SENT"
    EMAIL_SENT = "EMAIL_SENT"
    APPLIED = "APPLIED"
    UNKNOWN = "UNKNOWN"
    
    @classmethod
    def from_string(cls, state_str: str) -> 'JobApplicationState':
        """Create JobApplicationState from string"""
        try:
            return cls[state_str.upper()]
        except KeyError:
            return cls.UNKNOWN
    
    @classmethod
    def from_value(cls, value: int) -> 'JobApplicationState':
        """Create JobApplicationState from integer value"""
        try:
            return cls(value)
        except ValueError:
            return cls.UNKNOWN
