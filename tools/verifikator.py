"""Verifikator loader for SheerID tools."""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from inspect import signature
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class ToolSpec:
    module_path: str
    class_name: str


TOOL_SPECS: Dict[str, ToolSpec] = {
    "spotify": ToolSpec("spotify-verify-tool/main.py", "SpotifyVerifier"),
    "youtube": ToolSpec("youtube-verify-tool/main.py", "YouTubeVerifier"),
    "gemini": ToolSpec("one-verify-tool/main.py", "GeminiVerifier"),
    "perplexity": ToolSpec("perplexity-verify-tool/main.py", "PerplexityVerifier"),
    "boltnew": ToolSpec("boltnew-verify-tool/main.py", "BoltnewVerifier"),
    "k12": ToolSpec("k12-verify-tool/main.py", "K12Verifier"),
}


class Verifikator:
    """Load verifier classes from tool folders and run verification."""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).resolve().parent.parent

    def available_tools(self) -> list[str]:
        return sorted(TOOL_SPECS.keys())

    def verify(self, tool: str, url: str, proxy: Optional[str] = None) -> Dict[str, Any]:
        tool_key = tool.strip().lower()
        if tool_key not in TOOL_SPECS:
            raise ValueError(f"Tool tidak dikenal: {tool}")

        spec = TOOL_SPECS[tool_key]
        module = self._load_module(tool_key, spec.module_path)
        verifier_cls = getattr(module, spec.class_name)

        kwargs = {}
        try:
            if "proxy" in signature(verifier_cls.__init__).parameters:
                kwargs["proxy"] = proxy
        except (TypeError, ValueError):
            pass

        verifier = verifier_cls(url, **kwargs)

        if hasattr(verifier, "check_link"):
            check = verifier.check_link()
            if check is False:
                return {"ok": False, "stage": "check_link", "detail": "Link tidak valid"}

        result = verifier.verify()
        return {"ok": True, "result": result}

    def _load_module(self, tool_key: str, module_path: str):
        file_path = (self.base_dir / module_path).resolve()
        if not file_path.exists():
            raise FileNotFoundError(f"Module tool tidak ditemukan: {file_path}")

        module_name = f"tools_{tool_key}_module"
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Gagal memuat module: {file_path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
