
import unittest
import sys
import os
from unittest.mock import MagicMock

# Add current directory to path
sys.path.insert(0, os.getcwd())

# Mock dependencies before importing alpha_evolve
sys.modules["google"] = MagicMock()
sys.modules["google.generativeai"] = MagicMock()
sys.modules["dotenv"] = MagicMock()

from agent.aether_orchestrator.alpha_evolve import MutationGenerator

class TestAlphaEvolveSecurity(unittest.TestCase):
    def test_secret_redaction(self):
        """Test secret redaction in MutationGenerator (alpha_evolve)."""
        print("\n🧪 Testing Secret Redaction in alpha_evolve...")

        generator = MutationGenerator(use_gemini=False)

        secret_code = """
    def connect():
        api_key = "sk-1234567890abcdef"
        password = 'SuperSecretPassword'
        token: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        regular_var = "not_a_secret"
        short_secret = "pass"
        secret_with_spaces   =   "spaced_secret"
    """

        # Test Redaction
        redacted, secret_map = generator._redact_secrets(secret_code)

        self.assertNotIn("sk-1234567890abcdef", redacted)
        self.assertNotIn("SuperSecretPassword", redacted)
        self.assertNotIn("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9", redacted) # Should be redacted now
        self.assertNotIn("spaced_secret", redacted)

        self.assertIn("not_a_secret", redacted)
        self.assertNotIn('short_secret = "pass"', redacted) # Should be redacted (len >= 4)

        self.assertIn('token: str = "', redacted) # Check type hint structure preserved
        self.assertIn('secret_with_spaces   =   "', redacted) # Check spacing preserved

        self.assertEqual(len(secret_map), 5)
        self.assertTrue(any("sk-1234567890abcdef" == v for v in secret_map.values()))

        # Test Restoration
        restored = generator._restore_secrets(redacted, secret_map)
        self.assertEqual(restored, secret_code)

        print("✅ Secret Redaction tests passed (alpha_evolve)")

if __name__ == "__main__":
    unittest.main()
