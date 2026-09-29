# FDD Evaluation

This is a desktop app for writing an evaluation protocol for wind-turbine fault detection.

You use it to record how a method will be judged before you compare results. It saves that protocol, shows which answers are still missing, and suggests metrics that match the goal. It does not train a model. It does not run the detection algorithm.

## What you can do

You record the operational data, the evidence, any cost inputs, and the method under test.

You choose the main goal. The goals are early warning, maintenance planning, diagnostic quality, or cost and impact.

You describe the ground truth. That means what counts as a fault, how strong the evidence is, and why a case is treated as healthy.

You set the evaluation design. That covers the cases, the event windows, the training and test periods, the tuning rules, and the rule that turns alarms into a fault detection.

You pick the metrics. The app recommends a set, says why each metric fits, and notes its limits.

You can save the project as a `.fddx` file. You can also export the finished protocol as Markdown.

You can load one faulty case and one healthy case from CSV files. The app plots the series and scores CARE. CARE means Coverage, Accuracy, Reliability, and Earliness. If you enter site costs, it also compares the cost of acting early with the cost of waiting.

A glossary and a short reproducibility checklist are in the Help menu.

## Included examples

Three tutorials are in the File menu.

**Chapter 5** is a Care to Compare bearing-temperature protocol.

**Synthetic CUSUM pair** is a short faulty and healthy series for the case plots.

**Blade cost pair** is a simple blade-damage example with euro cost assumptions.

## How to run it

You need Python 3.12.

With conda:

```
conda env create -f environment.yml
conda activate fdd_eval
python -m fdd_eval
```

On Windows, `run.bat` starts the app after that environment exists.

With pip:

```
pip install -r requirements.txt
python -m fdd_eval
```

## How to build the Windows program

`build_exe.bat` uses PyInstaller and writes `dist\FDD_Evaluation.exe`. It uses the same conda environment.

## Project layout

`fdd_eval/` is the app.

`tutorials/` holds the three example projects and their data.

`scripts/` builds those tutorials and the app icon.

`tests/` checks the protocol logic. Run them with `pytest`.

`Background_Files/` holds reference notes used while the framework was written.

## License

MIT. See `LICENSE`.
