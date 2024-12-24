# Test creating and adding to tasks
echo y | ./main.py add 5 pushups --config config.toml
./main.py add 10 pushups --config config.toml
./main.py add 20 meditation --config config.toml --init-task

# Test that --init-task doesn't overwrite existing task
./main.py progress pushups --config config.toml  # Should show 15 total
./main.py add 0 pushups --config config.toml --init-task  # Try to reinit existing task
./main.py progress pushups --config config.toml  # Should still show 15 total

# Other tests
./main.py progress meditation --config config.toml
./main.py progress nonexistent --config config.toml
echo n | ./main.py add 5 squats --config config.toml
