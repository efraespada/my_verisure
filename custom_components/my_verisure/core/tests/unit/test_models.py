"""Unit tests for models - Legacy file for backward compatibility."""

import pytest

# This file is kept for backward compatibility but tests have been moved to:
# - test_auth_dto.py
# - test_installation_dto.py  
# - test_alarm_dto.py
# - test_session_dto.py
# - test_domain_models.py

# Import all tests to maintain compatibility
from .test_auth_dto import *
from .test_installation_dto import *
from .test_alarm_dto import *
from .test_session_dto import *
from .test_domain_models import *
