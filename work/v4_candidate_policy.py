"""Data-export eligibility only; this never grants visual/game acceptance."""
BLOCKED_PREFIXES=('needs_','requires_','historical','deferred')
def offline_export_eligible(candidate):
    status=candidate.get('status')
    return (candidate.get('offline_fit_passed') is True
            and isinstance(status,str) and bool(status)
            and not status.startswith(BLOCKED_PREFIXES))
