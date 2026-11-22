PY ?= .venv/bin/python
export PYTHONPATH := src

.PHONY: setup data score report all test clean
setup:
	uv venv --python 3.12 .venv && uv pip install -p .venv/bin/python -r requirements.txt
data:
	$(PY) -m hytte_finder.cli data
score:
	$(PY) -m hytte_finder.cli score
report:
	$(PY) -m hytte_finder.cli report
all: data score report
test:
	$(PY) -m pytest -q
