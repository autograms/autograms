#!/bin/bash
# File: proxy_apis/run_huggingface_cpu.sh
#
# Purpose:
#   Run Hugging Face TGI in CPU mode on a user-specified model and port.
#
# Usage:
#   bash proxy_apis/run_huggingface_cpu.sh <model-id> [port]
#
# Example:
#   bash proxy_apis/run_huggingface_cpu.sh tiiuae/falcon-7b-instruct 8081
#     -> Runs the Falcon model on CPU via port 8081
#
# Notes:
#   - This script does NOT require GPU drivers or nvidia-container-toolkit.
#   - Defaults to port 8080 if no port is specified.

script_dir="$(cd "$(dirname "$0")" && pwd)"

# Check if a model ID was provided
if [ -z "$1" ]; then
  echo "Error: No model ID provided."
  echo "Usage: bash proxy_apis/run_huggingface_cpu.sh <model-id> [port]"
  echo "Example: bash proxy_apis/run_huggingface_cpu.sh tiiuae/falcon-7b-instruct 8081"
  exit 1
fi

MODEL_ID=$1
PORT=${2:-8080}  # Default to 8080 if no port is provided

# Pull the Hugging Face TGI image
echo "Pulling Hugging Face TGI image..."
docker pull ghcr.io/huggingface/text-generation-inference:latest

# Run the TGI container in CPU mode
echo "Running Hugging Face TGI in CPU mode on port $PORT..."
docker run --shm-size 1g -p "$PORT:80" \
  ghcr.io/huggingface/text-generation-inference:latest \
  --model-id "$MODEL_ID" 
