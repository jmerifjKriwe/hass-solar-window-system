"""This file was consolidated into `tests/platforms/test_platforms.py`.

To avoid duplicate tests we skip collection of the legacy, file-local
platform tests which are now covered by the parametrised test suite.
"""

import pytest


pytest.skip("Consolidated in tests/platforms/test_platforms.py", allow_module_level=True)
