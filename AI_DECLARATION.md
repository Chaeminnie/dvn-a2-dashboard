# AI Declaration

## AI system used

**Claude** (Anthropic), accessed through claude.ai and Claude Code. No other AI system was used.

## How AI was used

Claude assisted with the development of three dashboards: SARS-CoV-2 variants and policy, gender data gaps in the World Development Indicators, and U.S. voter divides from 2016–2024 alongside Google search interest.

I used Claude to support technical implementation, code refinement, and drafting chart explanations and findings. I directed the project requirements and reviewed the proposed designs, code changes, and final outputs.

## My contribution

- **Planning and design:** Defined the subjects, audiences, research objectives, and visualisation direction. Evaluated proposed approaches and rejected ideas that did not fit the assessment requirements or project scope.
- **Data preparation:** Downloaded and exported the World Bank DataBank, Google Trends, MIT Election Lab, and Cooperative Election Study datasets, and ran the CES aggregation script locally.
- **Code review and optimisation:** Reviewed all three codebases using Claude Code, identifying redundant code, hardcoded values, and structural improvements, then reviewed the resulting changes.
- **Validation and quality assurance:** Checked data consistency, reviewed national election vote totals, and inspected rendered dashboards for visual and usability issues. I also reviewed the findings and limitations against the source data.

## Testing and verification

The supplied `grade_submission.py` checker was run with `--run-transform` on all three dashboards. Claude executed the checks in its workspace, and I reviewed the results. Each dashboard scored **70/70 on the automated assessment**. Visual issues identified through browser screenshots were corrected during iteration.

Data checks included ranges, duplicate keys, row counts, observation dates, and national vote totals. A double-counting issue in the election data was identified and corrected.

## Limitations and data sources

The WBL dashboard rescales annual weighted points to a 0–100 score. A comparison with the World Bank's WBL 2026 1.0 reference file confirmed the 2023 values for 129 economies without listed subsequent reforms or revisions. The remaining 55 differed; their individual differences have not all been independently verified. Earlier years (2000–2022) have not been checked against a published reference file.

The CES and MIT Election Lab data licences and Google Trends reuse conditions were checked against publisher sources. The relevant source files are included in the submission.

Claude supported implementation and review, while I directed the projects and evaluated the design decisions, code changes, data quality, and final outputs.