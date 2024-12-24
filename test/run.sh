# Test creating and adding to tasks
echo y | ./main.py add 5 pushups --config test/config.toml
./main.py add 10 pushups --config test/config.toml
./main.py add 20 meditation --config test/config.toml --init-task

# Test that --init-task doesn't overwrite existing task
./main.py progress pushups --config test/config.toml  # Should show 15 total
./main.py add 0 pushups --config test/config.toml --init-task  # Try to reinit existing task
./main.py progress pushups --config test/config.toml  # Should still show 15 total

# Other tests
./main.py progress meditation --config test/config.toml
./main.py progress nonexistent --config test/config.toml
echo n | ./main.py add 5 squats --config test/config.toml

rm -rf test-state
