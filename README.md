# Outlier — DATA1030 Group Project, Fall 2026

Team: **outlier**. Course: DATA1030 Hands-on Data Science, Brown University.

**Status:** topic selection and project planning. No topic has been selected, no full modeling dataset has been collected, and no model has been trained. Team member GitHub usernames and TA mentor are still to be recorded.

## Start here

- [Action plan / 工作大纲](docs/plans/2026-10-09-project-plan.md)
- [Dataset options / 数据选题比较](docs/dataset-options.md)
- [Midterm report outline / 报告提纲](report/outline.md)
- [Data documentation template](data/data-dictionary-template.md)
- [Source access checks](docs/source-checks.json)

## Course requirements

The group project is 35% of the course grade: 10 percentage points for the midterm report and 25 for the final presentation. The midterm report is due **October 25, 2026, at 5 pm on Gradescope**, with no grace period. The current rubric schedules final presentations during the week of December 7; presentation details are expected in early November.

The project must use a dataset collected through an API, web scraping, PDF extraction, or another method requiring coding effort. Direct use of ready-to-download Kaggle/UCI/data-repository datasets is not accepted. Document the actual collection procedure and keep the source and query details.

The midterm report has a maximum of 1,500 words, including figure/table captions but excluding references and appendix. It needs at least three explanatory visualizations and the prescribed sections. The report must be written by the team; the rubric permits LLM assistance for grammatical errors and typos, and prohibits LLM-written report text.

These files provide planning and an outline. They do not contain a submission-ready report.

## Repository layout

```text
data/       raw and processed data; data documentation
figures/    generated figures
results/    predictions, fitted models, and other analytical results
report/     midterm PDF and final presentation slides
src/        collection, preparation, EDA, and modeling code/notebooks
docs/       project planning and source feasibility checks
.gitignore
LICENSE
README.md
environment.yml
```

Large datasets can remain outside GitHub if the README gives an official source and exact collection/reproduction instructions. Add all team members as collaborators once their GitHub usernames are known. Do not commit credentials or unrelated personal files.

## Environment and reproduction status

`environment.yml` is copied from the course's current [data1030.yml](https://github.com/BrownDSI/DATA1030-fall2026/blob/main/data1030.yml), checked on October 9, 2026. The machine-specific `prefix` has been removed. Its specified versions include Python 3.14.6, NumPy 2.4.6, pandas 3.0.3, matplotlib 3.11.0, and scikit-learn 1.9.0; see the file for the complete specification.

The course environment has **not** been installed or verified in this checkout. Reuse your working course environment, or create the declared environment locally if needed. Update this section to the versions actually used when collection and analysis are implemented.

There is no analysis run command yet. Small source feasibility checks used Python 3.11.15 and the standard library (`urllib`, `json`); they verified access and basic field availability, not dataset-wide quality or predictive performance. Their summaries and query URLs are in `docs/source-checks.json`.

## License and sources

The MIT license applies to original project code and documentation. External data and third-party materials retain their original terms and attribution requirements.

- [Canvas syllabus](https://canvas.brown.edu/courses/1103554)
- [Official Fall 2026 midterm rubric](https://docs.google.com/document/d/1kC3cgE-CPUVmveWHdKAqlbnaq2XMNKjzY9ifF6M97ps/edit)
- [EdStem rubric announcement](https://edstem.org/us/courses/104806/discussion/8310956)
- [EdStem finalized team announcement](https://edstem.org/us/courses/104806/discussion/8358533)

Planning and repository setup were assisted by OpenAI Codex. The team owns the topic choice, collection implementation, interpretation, and submitted report.
