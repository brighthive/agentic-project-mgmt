"""SSL context cascade — works on Mac, Debian/Ubuntu, RHEL, and cron environments.

Resolution order (first match wins):
  1. truststore — uses the system trust store; preferred when installed
  2. certifi cert bundle — preferred when installed
  3. Distro CA bundles — /etc/ssl/cert.pem (Mac), Debian, RHEL paths
  4. SSL_CERT_FILE env var if set
  5. default Python context — works when system Python has its own cert store

Used by both the Jira REST client and Slack POST.
"""

from __future__ import annotations

import os
import ssl

# Distro-specific CA bundle locations. Order: Mac, Debian/Ubuntu, RHEL/CentOS.
_DISTRO_CA_BUNDLES: tuple[str, ...] = (
    "/etc/ssl/cert.pem",
    "/etc/ssl/certs/ca-certificates.crt",
    "/etc/pki/tls/certs/ca-bundle.crt",
)


def build_ssl_context() -> ssl.SSLContext:
    """Resolve a working SSL context across Mac/Linux + cron."""
    # truststore must inject *before* create_default_context so the resulting
    # context picks up the patched OS trust store.
    try:
        import truststore  # type: ignore[import-not-found]
        truststore.inject_into_ssl()
        return ssl.create_default_context()
    except ImportError:
        pass

    try:
        import certifi  # type: ignore[import-not-found]
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        pass

    cafile_env = os.environ.get("SSL_CERT_FILE")
    if cafile_env and os.path.exists(cafile_env):
        return ssl.create_default_context(cafile=cafile_env)

    for cafile in _DISTRO_CA_BUNDLES:
        if os.path.exists(cafile):
            return ssl.create_default_context(cafile=cafile)

    return ssl.create_default_context()
