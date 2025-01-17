#!/bin/bash
# File: run_huggingface_gpu.sh
#
# Usage:
#   bash run_huggingface_gpu.sh <model-id> [port]
#
# Example:
#   bash run_huggingface_gpu.sh tiiuae/falcon-7b-instruct 8081
#     -> Runs with model "tiiuae/falcon-7b-instruct" on port 8081
#
#   bash run_huggingface_gpu.sh tiiuae/falcon-7b-instruct
#     -> Runs with the given model on port 8080 (default).



script_dir="$(cd "$(dirname "$0")" && pwd)"

# Check if a model ID was provided as an argument
if [ -z "$1" ]; then
  echo "Error: No model ID provided."
  echo "Usage: bash run_tgi_gpu.sh <model-id> [port]"
  echo "Example: bash run_tgi_gpu.sh tiiuae/falcon-7b-instruct 8081"
  exit 1
fi

MODEL_ID=$1

# If a port was provided, use it. Otherwise default to 8080.
PORT=${2:-8080}

# Pull the Hugging Face TGI image
echo "Pulling Hugging Face TGI image..."
docker pull ghcr.io/huggingface/text-generation-inference:latest

echo "Running Hugging Face TGI with GPU on port $PORT..."
docker run --gpus all --shm-size 1g -p "$PORT:80" \
  ghcr.io/huggingface/text-generation-inference:latest \
  --model-id "$MODEL_ID" \
  --quantize eetq
