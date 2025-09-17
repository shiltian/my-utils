#!/bin/bash

# Exit on any error
set -e

cd /home/shiltian/Documents/vscode/my-utils/git-bisect

./build.sh

./run-in-docker.sh 8388b90e2dff
