#!/bin/bash

if [ "${RUNNER_DEBUG}" = "1" ]; then
    echo "Github actions: runner debug on"
    pytest --verbose --capture=no --timeout 60
else
    pytest
fi
