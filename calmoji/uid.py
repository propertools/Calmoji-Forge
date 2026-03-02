# calmoji/uid.py

import datetime
from hashlib import sha256


def generate_uid(dt: datetime.datetime, label: str, namespace: str = "calmoji") -> str:
    raw = f"{namespace}:{dt.isoformat()}:{label}"
    uid_hash = sha256(raw.encode("utf-8")).hexdigest()[:16]
    return f"{uid_hash}-{dt.strftime('%Y%m%dT%H%M%S')}@{namespace}.local"
