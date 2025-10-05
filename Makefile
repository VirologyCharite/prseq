test:
	make -C rust $@
	make -C python $@

clean:
	make -C rust $@
	make -C python $@

bumpversion:
	uv run bump2version patch
