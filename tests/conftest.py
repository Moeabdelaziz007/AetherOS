import sys
from unittest.mock import MagicMock

# Mock heavy/external dependencies that might not be present in the unit test environment
# or that we want to avoid using directly in unit tests.

# Mock firebase_admin and its submodules
mock_firebase_admin = MagicMock()
mock_firebase_admin.credentials = MagicMock()
mock_firebase_admin.firestore = MagicMock()
mock_firebase_admin.storage = MagicMock()
sys.modules["firebase_admin"] = mock_firebase_admin
sys.modules["firebase_admin.credentials"] = mock_firebase_admin.credentials
sys.modules["firebase_admin.firestore"] = mock_firebase_admin.firestore
sys.modules["firebase_admin.storage"] = mock_firebase_admin.storage

# Mock google.auth
mock_google = MagicMock()
mock_google.auth = MagicMock()
mock_google.cloud = MagicMock()
sys.modules["google"] = mock_google
sys.modules["google.auth"] = mock_google.auth
sys.modules["google.cloud"] = mock_google.cloud

# Mock redis
sys.modules["redis"] = MagicMock()
sys.modules["redis.asyncio"] = MagicMock()

# Mock numpy if missing
try:
    import numpy
except ImportError:
    sys.modules["numpy"] = MagicMock()

# Mock httpx if missing
try:
    import httpx
except ImportError:
    sys.modules["httpx"] = MagicMock()

# Mock other potentially missing or heavy libs
sys.modules["pyaudio"] = MagicMock()
sys.modules["mss"] = MagicMock()
sys.modules["PIL"] = MagicMock()
sys.modules["psutil"] = MagicMock()
