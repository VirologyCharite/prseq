test:
	make -C rust $@
	make -C python $@

clean:
	make -C rust $@
	make -C python $@
