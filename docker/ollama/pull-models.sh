#!/bin/bash

# Start Ollama in the background.
/bin/ollama serve &
pid=$!

# Wait for Ollama to start.
sleep 5

echo "Pulling llama3 model..."
ollama pull llama3
echo "Pulling nomic-embed-text model..."
ollama pull nomic-embed-text

# Wait for Ollama process to finish.
wait $pid
