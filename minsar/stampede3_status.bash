#!/bin/bash

# Show load averages using uptime
echo "=== SYSTEM LOAD AVERAGES ==="
uptime | awk -F'load average: ' '{print "Load averages (1 min, 5 min, 15 min): " $2}'
echo ""

# Show the number of running and waiting jobs using showq
echo "=== JOB QUEUE STATUS ==="
echo ""
/usr/local/bin/showq | tail -1
echo ""
