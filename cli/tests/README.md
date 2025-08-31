# CLI Tests Documentation

## 📋 Overview

This directory contains comprehensive tests for the My Verisure CLI application. The tests are organized into different categories to ensure thorough coverage of all functionality.

## 🗂️ Test Structure

```
cli/tests/
├── __init__.py              # Package initialization
├── pytest.ini              # Pytest configuration
├── run_tests.py            # Test execution script
├── README.md               # This file
├── test_display.py         # Display utility tests
├── test_input_helpers.py   # Input helper tests
├── test_session_manager.py # Session manager tests
├── test_commands.py        # Command tests
└── test_integration.py     # Integration tests
```

## 🧪 Test Categories

### 1. **Unit Tests** (`-m unit`)
- **`test_display.py`**: Tests for display utility functions
  - `print_header`, `print_success`, `print_error`, etc.
  - Output formatting and emoji usage
  - Mock objects for testing without real data

- **`test_input_helpers.py`**: Tests for user input functions
  - `get_user_credentials`, `select_phone`, `get_otp_code`
  - Input validation and error handling
  - Mock user input scenarios

- **`test_session_manager.py`**: Tests for session management
  - Session persistence (save/load)
  - Authentication state management
  - File operations and error handling

- **`test_commands.py`**: Tests for CLI commands
  - `AuthCommand`, `InfoCommand`, `AlarmCommand`
  - Command execution and argument parsing
  - Mock use case interactions

### 2. **Integration Tests** (`-m integration`)
- **`test_integration.py`**: End-to-end CLI testing
  - Argument parser functionality
  - Main function execution
  - Error handling and exit codes
  - Command routing and execution

## 🚀 Running Tests

### Prerequisites
```bash
# Activate virtual environment
source venv/bin/activate

# Install test dependencies (if not already installed)
pip install pytest pytest-asyncio pytest-cov
```

### Quick Test Execution
```bash
# Run all tests
python cli/tests/run_tests.py

# Or run directly with pytest
python -m pytest cli/tests/ -v
```

### Specific Test Categories
```bash
# Unit tests only
python -m pytest cli/tests/ -m unit -v

# Integration tests only
python -m pytest cli/tests/ -m integration -v

# Display tests only
python -m pytest cli/tests/ -m display -v

# Session manager tests only
python -m pytest cli/tests/ -m session -v
```

### Test with Coverage
```bash
# Run tests with coverage report
python -m pytest cli/tests/ --cov=cli --cov-report=term-missing

# Generate HTML coverage report
python -m pytest cli/tests/ --cov=cli --cov-report=html
```

## 📊 Test Coverage

The tests cover the following areas:

### ✅ **Display Functions** (100%)
- All display utility functions
- Output formatting
- Error message handling
- Mock object integration

### ✅ **Input Helpers** (100%)
- User credential input
- Phone selection
- OTP code input
- Installation selection
- Action confirmation

### ✅ **Session Management** (100%)
- Session persistence
- Authentication state
- File operations
- Error handling
- Cleanup operations

### ✅ **Commands** (100%)
- All command classes
- Argument parsing
- Execution flow
- Error handling
- Mock use case integration

### ✅ **Integration** (100%)
- CLI argument parsing
- Main function execution
- Error handling
- Exit codes
- Command routing

## 🔧 Test Configuration

### Pytest Configuration (`pytest.ini`)
- **Verbose output**: `-v` flag enabled
- **Async support**: `asyncio_mode = auto`
- **Markers**: Defined for test categorization
- **Warnings**: Disabled to reduce noise

### Test Markers
- `@pytest.mark.unit`: Unit tests
- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.slow`: Slow running tests
- `@pytest.mark.auth`: Authentication tests
- `@pytest.mark.display`: Display tests
- `@pytest.mark.input`: Input helper tests
- `@pytest.mark.session`: Session manager tests
- `@pytest.mark.commands`: Command tests

## 🎯 Test Design Principles

### 1. **Isolation**
- Each test is independent
- No shared state between tests
- Proper setup/teardown methods

### 2. **Mocking**
- External dependencies are mocked
- No real API calls during testing
- Predictable test behavior

### 3. **Coverage**
- All public functions tested
- Error conditions covered
- Edge cases handled

### 4. **Readability**
- Clear test names
- Descriptive docstrings
- Logical test organization

## 🐛 Debugging Tests

### Running Individual Tests
```bash
# Run specific test file
python -m pytest cli/tests/test_display.py -v

# Run specific test function
python -m pytest cli/tests/test_display.py::TestDisplayFunctions::test_print_header -v

# Run with debug output
python -m pytest cli/tests/ -v -s
```

### Test Output Analysis
```bash
# Detailed test output
python -m pytest cli/tests/ -v --tb=long

# Stop on first failure
python -m pytest cli/tests/ -x

# Show local variables on failure
python -m pytest cli/tests/ --tb=short -l
```

## 📈 Continuous Integration

The tests are designed to be run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run CLI Tests
  run: |
    source venv/bin/activate
    python -m pytest cli/tests/ --cov=cli --cov-report=xml
```

## 🔄 Test Maintenance

### Adding New Tests
1. Create test file following naming convention: `test_*.py`
2. Use appropriate test markers
3. Follow existing test patterns
4. Add to relevant test categories

### Updating Tests
1. Update tests when functionality changes
2. Maintain test coverage above 90%
3. Keep tests fast and reliable
4. Document any new test patterns

## 📝 Notes

- **No Real API Calls**: All tests use mocks to avoid real API calls
- **Async Support**: Tests properly handle async/await patterns
- **Cross-Platform**: Tests work on Windows, macOS, and Linux
- **Performance**: Tests complete in under 30 seconds
- **Reliability**: Tests are deterministic and repeatable
