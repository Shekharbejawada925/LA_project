# Contributing

This repository documents an academic CausalEdu learning analytics study. When proposing changes, describe the research question or bug, include reproducible steps, and distinguish original findings from new analyses.

## Reproduction checklist

1. Use Python 3.11 in an isolated environment.
2. Download the public CausalEdu dataset separately, following the data publisher's instructions.
3. Keep original CSV files in the ignored `data/` directory.
4. Run `python -I code/analysis.py data .` and `python -I code/build_report.py .` once the source files are available.
5. Check numerical findings against the submitted PDF before updating claims in the README.

Do not upload participant-identifying information or restricted educational records. Credit the dataset creators and all project contributors.
