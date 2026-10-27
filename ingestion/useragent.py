"""The one User-Agent every request to an outside service sends: the project contact only, never a personal one (CLAUDE.md rule).
A fork sets COURTCONNECT_USER_AGENT to its own project name and public URL (docs/fork_guide.md)."""
import os

USER_AGENT = os.environ.get("COURTCONNECT_USER_AGENT") or "courtconnect-ca/0.1 (+https://github.com/abov/courtconnect-ca)"
HEADERS = {"User-Agent": USER_AGENT}
