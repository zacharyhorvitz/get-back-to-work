#! /bin/bash

ollama serve &
sleep 20

# Run the script
python bugme.py --interval 5 --model_name "llava:7b" --prompt "Is there ANY social media (e.g. twitter, instagram, facebook, youtube, profiles, etc.) use in this screenshot? Yes or no?"
