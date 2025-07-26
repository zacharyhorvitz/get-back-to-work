"""
Takes screenshots, uses ollama, checks if you are slacking off. Pings you if you are.
"""

import mss
import datetime
import os
import subprocess
import time
import ollama
import re
import json
import argparse


def take_screenshot():
    """
    Take a screenshot and save it to the screen_captures directory.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_dir = os.path.join(os.path.dirname(__file__), "screen_captures")
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, f"screenshot_{timestamp}.png")

    with mss.mss() as sct:
        sct.shot(output=filepath)
        print(f"Saved screenshot to: {filepath}")
    return filepath


def write_info_about_screenshot(*, result, filepath):
    """
    Write info about the screenshot to a json file.
    """
    json_path = filepath.replace(".png", ".json")
    with open(json_path, "w") as f:
        f.write(
            json.dumps(
                {
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
                    "filepath": filepath,
                    "model_output": result['model_output'],
                    "verdict": result['verdict'],
                }
            )
        )


def clean_up_screenshot(filepath):
    """
    Clean up the screenshot and the json file.
    """
    try:
        os.remove(filepath)
        os.remove(filepath.replace(".png", ".json"))
    except Exception as e:
        print(f"Error cleaning up screenshot: {e}")


def notify(*, title, message):
    """
    Send a notification to the user.
    """
    subprocess.run(
        [
            "osascript",
            "-e",
            f'display notification "{message}" with title "{title}" sound name "default"',
        ]
    )


def ollama_call(
    *,
    filepath,
    model_name="llava:7b",
    prompt="What is this a screenshot of?",
    **model_kwargs,
):
    """
    Call the ollama model with the given filepath, model_name, prompt, and model_kwargs.
    """
    response = ollama.chat(
        model=model_name,
        messages=[{'role': 'user', 'content': prompt, 'images': [filepath]}],
        options=model_kwargs,
    )
    return response['message']['content']


def check_model_response(result):
    """
    Check the model response.
    """
    if re.search(r'yes', result, re.IGNORECASE):
        return True
    else:
        return False


def check_for_slacking(
    *,
    filepath,
    model_name="llava:7b",
    prompt="Is there ANY social media (e.g. twitter, instagram, facebook, youtube, profiles, etc.) use in this screenshot? Yes or no?",
    temperature=0.0,
):
    """
    Using the provided screenshot, check if the user is slacking off.
    """
    result = ollama_call(
        filepath=filepath, model_name=model_name, prompt=prompt, temperature=temperature
    )
    return dict(model_output=result, verdict=check_model_response(result))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval", type=int, default=30)
    parser.add_argument("--model_name", type=str, default="llava:7b")
    parser.add_argument(
        "--prompt",
        type=str,
        default="Is there ANY social media (e.g. twitter, instagram, facebook, youtube, profiles, etc.) use in this screenshot? Yes or no?",
    )
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--buffer_size", type=int, default=5)

    args = parser.parse_args()
    interval = args.interval
    buffer_size = args.buffer_size
    model_name = args.model_name
    prompt = args.prompt
    temperature = args.temperature

    print(f"Taking screenshots every {interval} seconds. Press Ctrl+C to stop.")
    time.sleep(10)
    screen_history = []

    try:
        while True:
            if len(screen_history) >= buffer_size:
                filepath = screen_history.pop(0)
                clean_up_screenshot(filepath)

            filepath = take_screenshot()
            screen_history.append(filepath)

            result = check_for_slacking(
                filepath=filepath,
                model_name=model_name,
                prompt=prompt,
                temperature=temperature,
            )
            write_info_about_screenshot(result=result, filepath=filepath)

            print(result['model_output'])
            print(result['verdict'])
            if result['verdict']:
                notify(title="Excuse me...", message="GO BACK TO WORK!")

            time.sleep(interval)
    except KeyboardInterrupt:
        print("Stopped.")


# Example usage:
# python bugme.py --interval 30 --model_name "llava:7b" --prompt "Is there ANY social media (e.g. twitter, instagram, facebook, youtube, profiles, etc.) use in this screenshot? Yes or no?" --buffer_size 5 --temperature 0.0

if __name__ == "__main__":
    main()
