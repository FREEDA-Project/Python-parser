for i in {1..5}
do
echo "-------- Iteration Number: $i"
python randomize_test/generator.py 2 2 30 randomize_test/
echo "-------- Generating Files"
time python main.py  randomize_test/cmp randomize_test/infr -b
done
