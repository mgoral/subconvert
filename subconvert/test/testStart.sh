echo 'May the Force be with you during SubConvert tests!'

TPATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SPATH="${TPATH}/.."

if [ ! -d 'log' ]; then
    echo "Creating log directory..."
    mkdir log
fi

sh clean.sh 2> /dev/null

echo "Running tests..."
for test in ./test_*.py
do
    TESTNAME=`basename ${test}`
    TESTNAME=${TESTNAME%.*}
    PYTHONPATH=${SPATH}:${PYTHONPATH} python3 ${test} 2>> log/${TESTNAME}.log
done

# Uncomment to enable other Python versions tests

#echo "Running Python 2.6 tests..."
#for p in ./test_*.py
#do
#    TESTNAME=`basename ${test}`
#    TESTNAME=${TESTNAME%.*}
#    PYTHONPATH=${SPATH}/src:${PYTHONPATH} python2.6 ${test} 2>> log/${TESTNAME}_26.log
#done

#echo "Running Python 2.7 tests..."
#for p in ./test_*.py
#do
#    TESTNAME=`basename ${test}`
#    TESTNAME=${TESTNAME%.*}
#    PYTHONPATH=${SPATH}/src:${PYTHONPATH} python2.7 ${test} 2>> log/${TESTNAME}_27.log
#done

echo -e "\n=============== [ Summary ] ==============="
for file in log/*.log
do
    echo "+-------------------------------------------"
    echo "| ${file}" 
    echo "+-------------------------------------------"
    grep -e 'ERROR: ' ${file}
    grep -e 'FAIL: ' ${file}
    grep -e '^OK$' ${file}
    echo
done
