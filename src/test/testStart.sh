cd ..
SPATH=`pwd`
cd -

if [ ! -d 'log' ]; then
    echo "Creating log directory..."
    mkdir log
fi

sh clean.sh

echo "Running tests..."
for test in ./test_*.py
do
    TESTNAME=`basename ${test}`
    TESTNAME=${TESTNAME%.*}
    PYTHONPATH=${SPATH}/src:${PYTHONPATH} python ${test} &>> log/${TESTNAME}.log
done

# Uncomment to enable other Python versions tests

#echo "Running Python 2.6 tests..."
#for p in ./test_*.py
#do
#    TESTNAME=`basename ${test}`
#    TESTNAME=${TESTNAME%.*}
#    PYTHONPATH=${SPATH}/src:${PYTHONPATH} python2.6 ${test} &>> log/${TESTNAME}_26.log
#done

#echo "Running Python 2.7 tests..."
#for p in ./test_*.py
#do
#    TESTNAME=`basename ${test}`
#    TESTNAME=${TESTNAME%.*}
#    PYTHONPATH=${SPATH}/src:${PYTHONPATH} python2.7 ${test} &>> log/${TESTNAME}_27.log
#done

echo -e "\n=============== [ Summary ] ==============="
for file in log/*.log
do
    echo "+-------------------------------------------"
    echo "| ${file}" 
    echo "+-------------------------------------------"
    grep -e 'ERROR: ' ${file}
    grep -e 'FAIL: ' ${file}
    grep -e 'PASS' ${file}
    echo
done
