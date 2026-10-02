import unittest
from review import review_text


class ContainerfileTests(unittest.TestCase):
    def test_mutable_remote_root(self):
        text = "FROM python:latest\nADD https://example.invalid/archive.tgz /tmp/\nUSER root\n"
        self.assertEqual({item["rule"] for item in review_text(text)}, {"mutable-base", "remote-add", "final-root-user"})

    def test_multi_stage_final_nonroot(self):
        digest = "a" * 64
        text = f"FROM example/build@sha256:{digest} AS build\nUSER root\nFROM scratch\nUSER 10001\nCOPY --from=build /app /app\n"
        self.assertEqual(review_text(text), [])

    def test_invalid_input(self):
        for value in ("RUN echo hello\n", "FROM alpine \\\n"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                review_text(value)
