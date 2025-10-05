test:
	cd rust && cargo test
	cd python && uv run pytest
