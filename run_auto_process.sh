#!/bin/bash

# Check if the environment variable file exists
if [ ! -f .env ]; then
    echo "Error: .env file does not exist. Please create and configure the .env file first."
    exit 1
fi

# Check if podcast_urls.txt exists
if [ ! -f podcast_urls.txt ]; then
    echo "Error: podcast_urls.txt file does not exist. Please create it and add podcast URLs."
    exit 1
fi

# Activate conda environment
echo "Activating conda environment..."
source ~/miniconda3/etc/profile.d/conda.sh
conda activate xyz

# Run the automatic processing script
echo "Starting podcast processing..."
python src/auto_process.py

# Deactivate conda environment
conda deactivate

echo "Processing complete!"
