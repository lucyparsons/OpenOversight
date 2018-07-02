#!/bin/bash
tail -f /tmp/geckodriver.log
/usr/local/bin/pytest -s -v tests/
