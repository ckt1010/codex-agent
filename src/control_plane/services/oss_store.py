from __future__ import annotations

from pathlib import Path


class LocalOSSStore:
    def __init__(self, root: str) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _to_local_path(self, uri_or_path: str) -> Path:
        if uri_or_path.startswith("oss://"):
            relative = uri_or_path.removeprefix("oss://")
            return self.root / relative
        return Path(uri_or_path)

    def put_text(self, key: str, content: str) -> str:
        path = self._to_local_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return key

    def get_text(self, uri: str) -> str:
        return self._to_local_path(uri).read_text(encoding="utf-8")
