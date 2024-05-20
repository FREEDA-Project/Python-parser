## Installation

### Requirements

- Python 3.x
- pip

First, create and activate a virtual environment:

```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

### Optional Requirements for Benchmarking

The following tools are optional and needed only for benchmarking:

- z3
- cbc
- minizinc

To install `pysmt` and check if `z3` is installed, run:

```bash
pysmt-install --check  # Check if z3 is installed
pysmt-install --z3     # Install z3
```
### Configuration for Benchmarking

For benchmarking, you also need to set some configuration paths in your script:

```python
CBC_SOLVER_PATH = "/path/to/cbc/executable"  # Path to the CBC executable
GECODE_PATH = "/path/to/gecode/executable"  # Path to the GECODE executable
```

## Usage


Before Using it , activate the Python virtual environment:

```bash
source env/bin/activate
```

### Generate Constraint Model

To generate the constraint model, run the following command:

```bash
python main.py randomize_test/cmp/3.yaml randomize_test/infr/6.yaml -f minizinc -o /tmp/out
```

- The first two parameters are the component file and the infrastructure file.
- The `-f` argument specifies the format and must be one of `smt`, `pulp`, `z3`, or `minizinc`.
- The `-o` flag specifies the output file. If omitted, the output is printed to the default standard output (except for `pulp`, which is not implemented).

### Benchmarking

#### Generating Random Samples


To generate random samples, use the following command:

```bash
# This command generates random samples, creating two directories inside random_test.
# It generates both components and infrastructure from 2 to 30 with a step of 1.
python randomize_test/generator.py 2 1 30 randomize_test/
```

#### Running Benchmarks

To run the benchmarks, use the following command:

```bash
# The -b for benchmarking,and can also accept directories.
python main.py randomize_test/cmp/ randomize_test/infr/ -b
```
