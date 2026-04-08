"""Application service — consolidate sources and export."""

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from models import Secret


@dataclass
class ConsolidateResult:
    total_secrets: int


class SecretsApp:
    def __init__(
        self,
        config,
        catalog,
        analyzer,
        backup_loader: Callable[[Path], list[Secret]],
        lastpass_client_factory: Callable[[], object],
    ):
        self.config = config
        self.catalog = catalog
        self.analyzer = analyzer
        self._backup_loader = backup_loader
        self._lastpass_factory = lastpass_client_factory

    def export_lastpass(self) -> list[Secret]:
        """Export all secrets from LastPass via client."""
        client = self._lastpass_factory()
        return client.export_all()

    def consolidate(
        self,
        skip_backup: bool = False,
        skip_lastpass: bool = False,
        materialize: bool = False,
    ) -> ConsolidateResult:
        count = 0
        if not skip_backup:
            for s in self._backup_loader(self.config.backup_dir):
                self.catalog.add(s)
                count += 1
        if not skip_lastpass:
            for s in self.export_lastpass():
                self.catalog.add(s)
                count += 1
        self.catalog.save()
        return ConsolidateResult(total_secrets=len(self.catalog.secrets))
