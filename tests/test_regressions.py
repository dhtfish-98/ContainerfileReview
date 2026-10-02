import json
import plistlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from review import review_text


class RegressionTests(unittest.TestCase):

    def test_root_group_and_stage_inheritance(self):
        self.assertEqual(review_text("FROM scratch\nUSER 0:1000\n")[0]["rule"],"final-root-user")
        self.assertEqual(review_text("FROM scratch AS first\nUSER 1000\nFROM first AS final\n"),[])
    def test_heredoc_content_does_not_change_docker_user(self):
        self.assertEqual(review_text("FROM scratch\nRUN <<'EOF'\nUSER 1000\nEOF\n")[0]["rule"],"final-root-user")
        self.assertEqual(review_text('FROM scratch\nRUN echo "<<EOF"\nUSER 1000\n'), [])
    def test_digest_escape_and_incomplete_instruction(self):
        self.assertIn("mutable-base",{x["rule"] for x in review_text("FROM alpine@sha256:invalid\nUSER 1000\n")})
        self.assertEqual(review_text("# escape=`\nFROM `\nscratch\nUSER 1000\n"),[])
        with self.assertRaises(ValueError): review_text("FROM scratch\nUSER 1000\nUSER\n")
