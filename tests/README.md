## How to test this facility




I used pytest for testing

to use the coverage test module: coverage_test.py 
I recommend to use:
- pytest --cov-report term-missing --cov=htcompact  tests/coverage_test.py

**This shows the coverage of all paths and the missing lines, \
you should get about 86%, at this moment (30.07.2020)**

The other tests modules should work just fine with:

- pytest "the_module"

To test all modules use:
- pytest tests

-> if you use this as well with coverage, it should scratch at the 100% mark.

### Requirements:
- pytest
- pytest-cov (for coverage tests)

#### Note:
you should always start a test from the source destination (htcompact/)
