"""Model agent adapter (gated) for Kortana.

This adapter is intentionally conservative: it will only attempt network calls
when `config.get('allow_network')` is truthy and a `model_endpoint` is set in
the config. The adapter uses `requests` for HTTP calls if enabled.

Usage:
  adapter = ModelAgentAdapter(config)
  resp = adapter.call_model("summarize this text")

The adapter logs what it would do to `memory` if provided and never performs
network actions unless explicitly enabled by config.
"""
from typing import Any, Dict, Optional
import json


class ModelAgentAdapter:
    def __init__(self, config: Dict[str, Any], memory=None):
        self.config = config or {}
        self.memory = memory

    def _log(self, text: str) -> None:
        if self.memory is not None:
            try:
                self.memory.add_note(text=text, source="model_agent_adapter")
            except Exception:
                pass

    def call_model(self, prompt: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Call the configured model endpoint with the prompt.

        Returns the parsed JSON response when successful, or None when the
        call was not performed (network disabled) or failed.
        """
        params = params or {}
        if not self.config.get("allow_network"):
            self._log("call_model: network-disabled - skipping model call")
            return None

        endpoint = self.config.get("model_endpoint")
        if not endpoint:
            self._log("call_model: no model_endpoint configured")
            return None

        # Attempt to import requests lazily to avoid a hard dependency at import time
        try:
            import requests
        except Exception:
            self._log("call_model: requests library not available")
            return None

        payload = {"prompt": prompt, "params": params}
        try:
            resp = requests.post(endpoint, json=payload, timeout=self.config.get("model_timeout", 15))
            if resp.status_code >= 200 and resp.status_code < 300:
                try:
                    return resp.json()
                except Exception:
                    return {"text": resp.text}
            else:
                self._log(f"call_model: non-2xx status {resp.status_code}")
                return None
        except Exception as e:
            self._log(f"call_model: exception {e}")
            return None
