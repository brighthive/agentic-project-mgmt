"""Duplicate detection and health scoring."""

from dataclasses import dataclass
from typing import Optional

from models import Secret


@dataclass
class DuplicateMatch:
    secret1: Secret
    secret2: Secret
    confidence: float
    reason: str


class SecretsAnalyzer:
    def find_duplicates(self, secrets: list[Secret]) -> list[DuplicateMatch]:
        out = []
        seen = []
        for s in secrets:
            for t in seen:
                if s.username == t.username and s.password == t.password:
                    out.append(DuplicateMatch(s, t, 1.0, "Identical credentials"))
                    break
                # Simple name similarity
                n1 = (s.name or "").lower()
                n2 = (t.name or "").lower()
                if n1 and n2 and (n1 in n2 or n2 in n1):
                    out.append(DuplicateMatch(s, t, 0.9, "Similar names"))
                    break
            seen.append(s)
        return out

    def suggest_deprecation(self, secret: Secret) -> tuple[bool, str]:
        if "deprecated" in (secret.name or "").lower():
            return True, "Name contains 'deprecated'"
        return False, ""

    def get_health_score(self, secrets: list[Secret]) -> dict:
        dups = self.find_duplicates(secrets)
        dep_count = sum(1 for s in secrets if self.suggest_deprecation(s)[0])
        score = max(0, 100 - len(dups) * 10 - dep_count * 5)
        return {
            "overall_score": min(100, score),
            "total_secrets": len(secrets),
            "duplicates": len(dups),
            "deprecated": dep_count,
        }
