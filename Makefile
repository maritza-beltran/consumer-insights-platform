.PHONY: setup data validate build app test clean

export MPLCONFIGDIR := $(CURDIR)/.matplotlib

setup:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt

data:
	.venv/bin/python src/generate_data.py

validate:
	.venv/bin/python src/validate_data.py

build:
	.venv/bin/python src/build_outputs.py

app:
	.venv/bin/streamlit run app/streamlit_app.py

test:
	.venv/bin/pytest tests/ -v

clean:
	rm -rf data/raw/*.csv data/processed/*.csv data/processed/*.parquet
	rm -rf outputs/tables/* outputs/charts/*
