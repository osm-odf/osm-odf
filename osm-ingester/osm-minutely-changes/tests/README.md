# OSM Minutely Changes Tests

This directory contains tests for the OSM Minutely Changes consumer.

## Running the Tests

To run the tests, follow these steps:

1. Install the test dependencies:
```
pip install -r ../test_requirements.txt
```

2. Run all tests:
```
python -m pytest
```

3. Run tests with coverage report:
```
python -m pytest --cov=../
```

## Test Structure

- `test_consumer.py`: Tests for the main consumer logic in `consumer.py`

## Mocking

The tests use the `mock` library to mock the `osmdiff` module, since it relies on external data sources. The tests focus on the internal processing logic rather than the actual retrieval of OSM data.

## Environment Variables

The tests set various environment variables such as `VERBOSE`, `NODES`, `WAYS`, etc. to test different output modes. These are reset after each test to avoid interference between tests.