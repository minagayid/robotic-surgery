from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from robotic_os.local_model import LocalModelClient


class LocalModelTests(unittest.TestCase):
    def test_client_is_disabled_without_a_local_endpoint(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            client = LocalModelClient.from_env()
        self.assertFalse(client.available)

    def test_endpoint_normalizes_to_chat_completions(self) -> None:
        client = LocalModelClient("http://127.0.0.1:11434/v1", "gpt-oss-20b")
        self.assertEqual(client.chat_url, "http://127.0.0.1:11434/v1/chat/completions")

    def test_remote_endpoint_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            LocalModelClient("https://example.com/v1", "model")


if __name__ == "__main__":
    unittest.main()
