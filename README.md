# ethsim

![example workflow](https://github.com/github/ferencberes/ethsim/actions/workflows/main.yml/badge.svg)

## Installation

Create your conda environment:
```bash
conda create -n ethsim python=3.8
```

Activate your environment, then install Python dependencies:
```bash
conda activate ethsim
pip install -r reuirements.txt
```

## Tests

Run the following command before pushing new commits to the repository!
```bash
cd tests
pytest
```