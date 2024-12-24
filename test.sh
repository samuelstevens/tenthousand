echo y | ./main.py add 5 pushups --config config.toml
./main.py add 10 pushups --config config.toml
./main.py add 20 meditation --config config.toml --init-task
./main.py progress pushups --config config.toml
./main.py progress meditation --config config.toml
./main.py progress nonexistent --config config.toml
echo n | ./main.py add 5 squats --config config.toml
