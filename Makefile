.PHONY: install test lint format-check dashboard demo demo-ci demo-handoff demo-ci-fail demo-init-ci clean-reports

install:
	pip install -e ".[dev]"

test:
	pytest

lint:
	ruff check .

format-check:
	ruff format --check .

dashboard:
	streamlit run app.py

demo:
	cbg compare-files examples/baseline.json examples/current.json --threshold 10 --directions-config examples/directions.json --report reports/report.md --html-report reports/report.html --codex-prompt reports/codex_fix_prompt.md

demo-ci:
	cbg compare-files examples/baseline.json examples/current_no_regression.json --threshold 10 --directions-config examples/directions.json --report reports/report.md --html-report reports/report.html --fail-on-regression

demo-handoff:
	cbg handoff-pack --baseline examples/baseline.json --current examples/current.json --directions-config examples/directions.json --threshold 10 --direction higher_is_worse --output-dir reports/handoff

demo-init-ci:
	PYTHONPATH=src python -m codex_benchmark_guardian.cli init-ci --output reports/benchmark_guardian_ci.yml

demo-ci-fail:
	@output=$$(mktemp); \
	if cbg compare-files examples/baseline.json examples/current.json --threshold 10 --directions-config examples/directions.json --report reports/report.md --html-report reports/report.html --fail-on-regression >$$output 2>&1; then \
		cat $$output; \
		rm -f $$output; \
		echo "Expected benchmark regressions, but the comparison passed."; \
		exit 1; \
	else \
		status=$$?; \
		cat $$output; \
		if grep -q "benchmark regression" $$output; then \
			rm -f $$output; \
			echo "CI correctly failed because benchmark regressions were detected."; \
		else \
			rm -f $$output; \
			exit $$status; \
		fi; \
	fi

clean-reports:
	rm -f reports/report.md reports/report.html reports/codex_fix_prompt.md reports/benchmark_guardian_ci.yml
	rm -rf reports/handoff
