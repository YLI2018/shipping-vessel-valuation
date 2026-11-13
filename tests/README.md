# Automated tests

This folder will contain tests for model calculations,
data checks and expected behaviour.

- `test_age_curve.py`: M1 published results and refusal of bad input (5 tests).
- `test_hedonic.py`: M1+ published results.
- `test_dcf.py`: M2 published results and behaviour (8 tests).

Run all: `python3 -m unittest discover -s tests`
