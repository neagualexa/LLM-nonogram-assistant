#!/bin/bash

# Check if Conda is installed
if ! [ -x "$(command -v conda)" ]; then
  echo 'Error: Conda is not installed.' >&2
  exit 1
fi

# Check if Conda environment exists
if conda env list | grep -q 'venvpy'; then
  echo 'Conda environment exists'
else
  echo 'Conda environment does not exist, Creating... [venvpy]'
  # Create a Conda environment
  conda create -n venvpy python=3.7
  echo 'Conda environment created [venvpy]'
fi

# Activate the Conda environment
conda activate venvpy

# Install requirements
pip install -r requirements.txt

# Start first Flask server
python app.py &

# Save PID of first server
pid1=$!

# Start second Flask server
python speech_pipeline/server.py &

# Save PID of second server
pid2=$!

# Wait for both servers to finish
wait $pid1 $pid2

# Deactivate the Conda environment
conda deactivate

echo "Both Flask servers have stopped"