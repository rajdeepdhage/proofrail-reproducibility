.PHONY: verify test manifest h4 release-check

verify:
	bash scripts/verify.sh

test:
	python3 -m unittest discover -s tests -v

manifest:
	python3 scripts/make_manifest.py

h4:
	python3 metrics/h4_distribution_test.py --json benchmark/results/h4_distribution_test.json

release-check:
	python3 scripts/check_release_readiness.py
