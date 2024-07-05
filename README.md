# Requirements
- Python 3.11.4
- Pip

# Setup
Create and activate a virtual environment:
```bash
python3 -m venv env
source ./env/bin/activate
pip install -r requirements.txt
```

# Usage
First, activate the Python virtual environment:

```bash
source ./env/bin/activate
```
Then run the program
```bash
python main.py data/components_v0.2.yaml data/infrastructure_v0.1.yaml -f minizinc
```
where `data/components_v0.2.yaml` is the YAML file containing the application
definition and `infrastructure_v0.1.yaml` contains the infrastructure.

## Options
Possible options are:
- `-f`, `--format`: specifies the output format. Possible values are `smt`,
  `ampl`, or `minizinc` (default, and the only one currently supported).
- `-p`, `--flavour-priority`: specifies the possible proprity strategy for
  flavours. Possible values are: `manual` (meaning that the user must specify
  insidtehe application YAML a total order for each flavour based on the
  priority), `lexicographic`, `reversed` or `incremental` (default).
- `-r`, `--additional-resources`: specifies a file path to additional resources.
  An example can be found at `data/resources_example.yaml`.
