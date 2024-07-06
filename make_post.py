import os
import argparse
import time
from dotenv import load_dotenv
from parse_extracted import get_show_data

load_dotenv()

header = """
Weekly superautomated AI recap of the most discussed shows on "What are you watching and what do you recommend?".

This week's top shows:
"""

footer = f"""
Code and data open-source on [GitHub](https://github.com/AlexanderDzhoganov/reddit-tv-summary).
Last update @ {time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())}.
"""


def main(args):
    if not os.path.exists(os.path.dirname(args.output_path)):
        os.makedirs(os.path.dirname(args.output_path))

    filenames = [f for f in os.listdir(args.input_path) if f.endswith(".txt")]

    shows = []

    for filename in filenames:
        show_id = filename.split(".")[0]
        show_data = get_show_data(show_id)
        summary = ""
        with open(os.path.join(args.input_path, filename), "r") as f:
            summary = f.read()

        shows.append((show_data["name"], summary))

    # sort by name alphabetically
    shows = sorted(shows, key=lambda x: x[0])

    with open(args.output_path, "w") as f:
        f.write(f"{header}\n")

        for show_name, summary in shows:
            f.write(f"**{show_name}**\n\n")
            f.write(f"{summary}\n\n")
            f.flush()

        f.write(f"{footer}\n")

    print(f"Saved {len(shows)} shows to {args.output_path}")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_path", type=str, required=True)
    parser.add_argument("--output_path", type=str, required=True)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    main(args)
