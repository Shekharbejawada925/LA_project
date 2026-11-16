# Methods and Reproduction

## Source data

Obtain the CausalEdu data from [Eedi/CausalEdu](https://github.com/Eedi/CausalEdu). The original submitted script expects:

- `checkins_lessons_checkouts_training.csv`
- `student_metadata.csv`
- `construct_experiments_ates_test.csv`
- `checkin_to_checkout.csv`
- `construct_prerequisites_test.csv`

Place these in the local ignored `data/` directory. No private learner records should be committed.

## Analysis pipeline

1. Sort learning events by learner and timestamp; construct pre-event check-in history.
2. Join session sequences to check-ins, retries, lesson events and check-outs.
3. Compute construct-level features: initial accuracy, prior mastery, retry recovery, lesson uptake and lesson gain.
4. Build a directed expert-prerequisite graph and shortest-path distance features.
5. Match 88 randomized experiments to the corresponding observational lesson/question pairs.
6. Compare naive rates with randomized ATEs using paired differences, confidence intervals and statistical tests (H1).
7. Compare analytical guessing correction, plain gains, ridge, gradient boosting and a constant mean-ATE baseline using repeated grouped cross-validation (H2).
8. Examine year-group/prerequisite-distance variation and prior-mastery descriptive patterns (H3).
9. Produce summary CSV/JSON files and the four figures; generate the academic PDF from those outputs.

## Intended directory structure

```text
data/                              # downloaded separately
code/analysis.py                   # originally submitted analysis script
code/build_report.py               # original report builder
results/                            # generated CSV/JSON
figures/                            # original generated figures
report/final_report.pdf             # generated academic report
```

## Commands

```bash
python -m venv .venv
# Activate the environment for your OS
pip install -r requirements.txt
python -I code/analysis.py data .
python -I code/build_report.py .
```

The original scripts are preserved in the complete portfolio ZIP supplied with the project. Until the scripts are uploaded to this GitHub repository, the commands above will not run from a fresh GitHub clone.

## Reproducibility caveats

The original program fixes its random seed. Output can still depend on the exact dataset release and library versions; the academic report describes experimental ATEs as noisy and the sample as small.
