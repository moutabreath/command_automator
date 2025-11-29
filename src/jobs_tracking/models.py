from enum import Enum


class JobApplicationState(Enum):
    CONNECTION_REQUESTED = 1
    MESSAGE_SENT = 2
    EMAIL_SENT = 3
    APPLIED = 4
    UKNOWN = 5