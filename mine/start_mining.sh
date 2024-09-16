#!/bin/bash

cleanup() {
    echo "Stoping processes"
    kill $(jobs -p)  
    wait 
    echo "All processes have been stopped."
}

trap cleanup SIGINT

sleep 10

python3 server.py &
sleep 5

# Apply a process for each core (define yours) 
python3 mine.py 1 --stop-on-block &
# python3 mine.py 2 &
# python3 mine.py 3 &
# python3 mine.py 4 &


wait
