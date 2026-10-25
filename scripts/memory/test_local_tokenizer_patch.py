#!/usr/bin/env python3
"""Offline regression for the explicit Cognee patch; run in its pinned runtime.

Requires HUGGINGFACE_TOKENIZER pointing to a read-only local BAAI snapshot.
The reviewed patch must be applied to a disposable copy of the verified source.
No model weights, database, credentials, runtime monkeypatch or network allowed.
"""
import ast
import inspect
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

NETWORK_ATTEMPTS = []


def reject_network(event, _args):
    if event in {"socket.connect", "socket.getaddrinfo"}:
        NETWORK_ATTEMPTS.append(event)
        raise RuntimeError("Network forbidden in tokenizer regression")


sys.addaudithook(reject_network)

from cognee.infrastructure.databases.vector.embeddings.config import EmbeddingConfig
from cognee.infrastructure.databases.vector.embeddings.FastembedEmbeddingEngine import (
    FastembedEmbeddingEngine,
)
from cognee.infrastructure.llm.tokenizer.HuggingFace import HuggingFaceTokenizer
from cognee.infrastructure.llm.tokenizer.resolver import resolve_embedding_tokenizer


class LocalTokenizerRegression(unittest.TestCase):
    def setUp(self):
        self.snapshot = Path(os.environ["HUGGINGFACE_TOKENIZER"])

    def tearDown(self):
        self.assertEqual(NETWORK_ATTEMPTS, [], "Unexpected network/fallback")

    def resolve(self, path):
        return resolve_embedding_tokenizer(
            provider="fastembed", model="BAAI/bge-small-en-v1.5",
            huggingface_tokenizer=str(path),
        )

    def copy_fixture(self, directory):
        for name in ("tokenizer.json", "tokenizer_config.json", "special_tokens_map.json", "vocab.txt"):
            shutil.copyfile(self.snapshot / name, directory / name)

    def test_environment_reaches_embedding_config(self):
        self.assertEqual(EmbeddingConfig().huggingface_tokenizer, str(self.snapshot))

    def test_factory_passes_override_to_fastembed(self):
        # Check propagation without initializing or loading embedding weights.
        import importlib
        factory = importlib.import_module(
            "cognee.infrastructure.databases.vector.embeddings.get_embedding_engine"
        )
        tree = ast.parse(inspect.getsource(factory.create_embedding_engine))
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
                 and isinstance(node.func, ast.Name) and node.func.id == "FastembedEmbeddingEngine"]
        self.assertEqual(len(calls), 1)
        self.assertTrue(any(k.arg == "huggingface_tokenizer"
                            and isinstance(k.value, ast.Name)
                            and k.value.id == "huggingface_tokenizer"
                            for k in calls[0].keywords))
        init = ast.parse(inspect.getsource(sys.modules[FastembedEmbeddingEngine.__module__]))
        self.assertTrue(any(isinstance(n, ast.Assign)
                            and isinstance(n.value, ast.Name)
                            and n.value.id == "huggingface_tokenizer"
                            and any(isinstance(t, ast.Attribute)
                                    and t.attr == "huggingface_tokenizer" for t in n.targets)
                            for n in ast.walk(init)))

    def test_resolver_uses_local_wordpiece(self):
        tokenizer = self.resolve(self.snapshot)
        self.assertIsInstance(tokenizer, HuggingFaceTokenizer)
        tokens = tokenizer.extract_tokens("Synthetic tokenizer fixture.")
        self.assertGreater(len(tokens), 0)
        self.assertEqual(tokenizer.count_tokens("Synthetic tokenizer fixture."), len(tokens))
        self.assertEqual(tokenizer.model_input_limit, 510)

    def test_engine_get_tokenizer_preserves_override(self):
        # Exercise this method alone: no embedding weights or engine initialization.
        engine = FastembedEmbeddingEngine.__new__(FastembedEmbeddingEngine)
        engine.model = "BAAI/bge-small-en-v1.5"
        engine.huggingface_tokenizer = str(self.snapshot)
        tokenizer = engine.get_tokenizer()
        self.assertIsInstance(tokenizer, HuggingFaceTokenizer)
        self.assertGreater(tokenizer.count_tokens("Synthetic fixture."), 0)

    def test_remote_override_fails_closed(self):
        with self.assertRaises(ValueError):
            self.resolve("BAAI/bge-small-en-v1.5")

    def test_missing_snapshot_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                self.resolve(Path(directory) / "absent")

    def test_missing_metadata_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                self.resolve(Path(directory))

    def test_corrupt_metadata_fails_without_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            self.copy_fixture(path)
            (path / "tokenizer.json").write_text("not-json")
            with self.assertRaises(Exception):
                self.resolve(path)

    def test_symlink_snapshot_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "link"
            path.symlink_to(self.snapshot, target_is_directory=True)
            with self.assertRaises(ValueError):
                self.resolve(path)

    def test_symlink_metadata_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            self.copy_fixture(path)
            (path / "tokenizer.json").unlink()
            (path / "tokenizer.json").symlink_to(self.snapshot / "tokenizer.json")
            with self.assertRaises(ValueError):
                self.resolve(path)


if __name__ == "__main__":
    unittest.main()
