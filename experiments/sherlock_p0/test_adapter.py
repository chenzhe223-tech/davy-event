import unittest
from unittest.mock import patch, Mock
from experiments.sherlock_p0.adapter import validate_username, build_command, parse_found, run

class AdapterTests(unittest.TestCase):
    def test_valid_username(self):
        self.assertEqual(validate_username("davylab_01"), "davylab_01")
    def test_reject_injection(self):
        for name in ("abc;rm -rf /", "../hello", "a b", ""):
            with self.assertRaises(ValueError):
                validate_username(name)
    def test_site_validation(self):
        with self.assertRaises(ValueError):
            build_command("davylab", ["GitHub;echo bad"])
    def test_command_no_shell(self):
        cmd = build_command("davylab", ["GitHub"])
        self.assertEqual(cmd[-3:], ["--site", "GitHub", "davylab"])
    def test_parse_dedup(self):
        text = "[+] GitHub: https://github.com/example\n[+] GitHub: https://github.com/example\n[-] Other: none"
        self.assertEqual(len(parse_found(text)), 1)
        self.assertEqual(parse_found(text)[0]["status"], "candidate_unverified")
    @patch("experiments.sherlock_p0.adapter.subprocess.run")
    def test_run_mocked(self, mock_run):
        mock_run.return_value = Mock(returncode=0, stdout="[+] GitHub: https://github.com/example", stderr="")
        result = run("davylab", ["GitHub"])
        self.assertEqual(result["status"], "completed")
        self.assertEqual(len(result["accounts"]), 1)
        self.assertFalse(mock_run.call_args.kwargs["check"])
        self.assertNotIn("shell", mock_run.call_args.kwargs)
    @patch("experiments.sherlock_p0.adapter.subprocess.run", side_effect=__import__("subprocess").TimeoutExpired("sherlock", 2))
    def test_timeout(self, _):
        self.assertEqual(run("davylab")["status"], "timeout")

if __name__ == "__main__":
    unittest.main()
