"""LastPass client — uses lpass CLI to export vault."""

import csv
import subprocess
import uuid
from pathlib import Path

from models import Secret


class LastPassClient:
    """Export LastPass vault via lpass (LastPass CLI)."""

    def export_all(self) -> list[Secret]:
        """Run lpass export and parse CSV into Secret objects."""
        try:
            result = subprocess.run(
                ["lpass", "export"],
                capture_output=True,
                text=True,
                timeout=60,
            )
        except FileNotFoundError:
            raise RuntimeError(
                "lpass CLI not found. Install: https://github.com/lastpass/lastpass-cli"
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("lpass export timed out")

        if result.returncode != 0:
            raise RuntimeError(f"lpass export failed: {result.stderr or result.stdout}")

        return self._parse_csv(result.stdout)

    def _parse_csv(self, text: str) -> list[Secret]:
        """Parse lpass CSV format: url,username,password,extra,name,grouping."""
        out = []
        reader = csv.reader(text.splitlines())
        for i, row in enumerate(reader):
            if len(row) < 5:
                continue
            url, username, password, extra, name, *rest = row + [""] * 6
            grouping = (rest[0] or "") if rest else ""
            secret = Secret(
                id=str(uuid.uuid4()),
                name=name or f"Unknown-{i}",
                username=username,
                password=password,
                url=url,
                notes=extra,
                grouping=grouping,
            )
            out.append(secret)
        return out
