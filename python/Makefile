test:
	uv run pytest

clean:
	find . \( -name '*.pyc' -o -name '*~' \) -print0 | xargs -r -0 rm
	find . -name '__pycache__' -type d -print0 | xargs -r -0 rm -r
	find . -name '.pytest_cache' -type d -print0 | xargs -r -0 rm -r
	find . -name '.ruff_cache' -type d -print0 | xargs -r -0 rm -r
	rm -fr build dist

clobber: clean
	rm -fr .nox
