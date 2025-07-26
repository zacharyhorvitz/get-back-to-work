#! /bin/bash

# Install dependencies
pip install -r requirements.txt

# Pull the ollama model
ollama pull llava:7b
