test:
	make -C rust $@
	make -C python $@

clean:
	make -C rust $@
	make -C python $@

bumpversion:
	uv run bump2version patch

wc:
	wc -l c/*.c python/src/prseq/*.py python/src/*.rs python/tests/*.py rust/src/*.rs rust/tests/*.rs
