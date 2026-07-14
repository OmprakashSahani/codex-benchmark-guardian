.PHONY: install test lint format-check demo demo-ci clean-reports

install:
	pip install -e ".[dev]"

test:
	pytest

lint:
	ruff check .

format-check:
	ruff format --check .

demo:
	cbg compare-files examples/baseline.json examples/current.json --threshold 10 --directions-config examples/directions.json --report reports/report.md --html-report reports/report.html

demo-ci:
	cbg compare-files examples/baseline.json examples/current.json --threshold 10 --directions-config examples/directions.json --report reports/report.md --html-report reports/report.html --fail-on-regression

clean-reports:
	rm -f reports/report.md reports/report.html
