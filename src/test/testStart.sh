cd ..
SPATH=`pwd`
cd -

if [ -d 'log' ]; then
    mkdir log
fi

echo "Running tests..."
PYTHONPATH=${SPATH}/src:${PYTHONPATH} python test_parsers.py &> log/test_parsers.log &> log/test_parsers.log
grep -e 'FAIL: ' log/test_parsers.log
echo

echo "Running Python 2.6 tests..."
PYTHONPATH=${SPATH}/src:${PYTHONPATH} python2.6 test_parsers.py &> log/test_parsers26.log
grep -e 'FAIL: ' log/test_parsers.log
echo

echo "Running Python 2.7 tests..."
PYTHONPATH=${SPATH}/src:${PYTHONPATH} python2.7 test_parsers.py &> log/test_parsers27.log
grep -e 'FAIL: ' log/test_parsers.log
echo
