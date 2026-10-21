"""The one User-Agent every request to an outside service sends: the project contact only, never a personal one (CLAUDE.md rule)."""
USER_AGENT = "courtconnect-ca/0.1 (+https://github.com/abov/courtconnect-ca)"
HEADERS = {"User-Agent": USER_AGENT}
