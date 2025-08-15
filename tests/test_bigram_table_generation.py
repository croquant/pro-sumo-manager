"""Tests for generating bigram tables from shikona corpus."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from unittest.mock import patch

from django.test import SimpleTestCase

from libs.generators.name import (
    DIRNAME,
    generate_name_char_bigram_table,
)


class BigramTableGenerationTests(SimpleTestCase):
    """Ensure bigram tables are generated correctly."""

    def test_bigram_table_matches_fixture(self) -> None:
        """Generated table matches the committed fixture."""
        data_dir = os.path.join(DIRNAME, "data")
        corpus = os.path.join(data_dir, "shikona_corpus.txt")
        fixture = os.path.join(data_dir, "name_char_bigram_table.json")
        with tempfile.TemporaryDirectory() as tmpdir:
            dest = os.path.join(tmpdir, "out.json")
            generate_name_char_bigram_table(corpus, dest)
            with open(dest, encoding="utf-8") as f:
                generated = json.load(f)
        with open(fixture, encoding="utf-8") as f:
            expected = json.load(f)
        self.assertEqual(generated, expected)

        for entry in generated["bigrams"].values():
            self.assertIn("end", entry)
            total_prob = entry["end"] + sum(p for _, p in entry["chars"])
            self.assertAlmostEqual(total_prob, 1.0, places=6)

        # Cover default path usage
        with tempfile.TemporaryDirectory() as tmpdir:
            data_tmp = os.path.join(tmpdir, "data")
            os.makedirs(data_tmp)
            shutil.copy(corpus, os.path.join(data_tmp, "shikona_corpus.txt"))
            with patch("libs.generators.name.DIRNAME", tmpdir):
                generate_name_char_bigram_table()
            with open(
                os.path.join(data_tmp, "name_char_bigram_table.json"),
                encoding="utf-8",
            ) as f:
                generated_default = json.load(f)
        self.assertEqual(generated_default, expected)
