.PHONY: setup data validate build app test clean

setup:
	pip install -r requirements.txt

data:
	python src/generate_data.py

validate:
	python src/validate_data.py

build:
	python src/build_outputs.py

app:
	streamlit run app/streamlit_app.py

test:
	pytest tests/ -v

clean:
	rm -rf data/raw/*.csv data/processed/*.csv data/processed/*.parquet
	rm -rf outputs/tables/* outputs/charts/*
