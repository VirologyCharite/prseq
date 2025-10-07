# Note that the C code isn't used to support the Python interface. It is
# present in the project for the purposes of benchmarking (i.e., for
# informally testing the speed of the Rust/Python combination). So 'make
# test' is not automatically run in the 'c' directory because that would
# assume you have gcc installed, which may not be the case.
test:
	make -C rust $@
	make -C python $@

publish: bumpversion
	git push origin main --tags

clean:
	find . -name '*~' -print0 | xargs -r -0 rm
	make -C c $@
	make -C python $@
	make -C rust $@

# bumpversion will make changes to five files, commit them, then tag with a
# version like v0.0.12.
bumpversion:
	uv run bump2version patch

wc:
	wc -l \
            c/*.c \
            python/src/*.rs \
            python/src/prseq/*.py \
            python/tests/*.py \
            rust/src/*.rs \
            rust/tests/*.rs
