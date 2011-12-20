SPATH=${HOME}/Programy/python/subconvert

test:
	PYTHONPATH=${SPATH}/src:${PYTHONPATH} python test_parsers.py

test26:
	PYTHONPATH=${SPATH}/src:${PYTHONPATH} python2.6 test_parsers.py

test27:
	PYTHONPATH=${SPATH}/src:${PYTHONPATH} python2.7 test_parsers.py

clean:
	rm -f subs/Assert_*
	rm -f subs/Test_*

cleantest:
	make test 
	make clean

