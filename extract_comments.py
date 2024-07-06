import os
import argparse
import json
from dotenv import load_dotenv
from openai import OpenAI
import tiktoken
import random
import re
from tqdm import tqdm

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

system_message = """
You are given a comment thread from a Reddit post about TV shows.
Assign the info from the comments to the TV show name.
Copy it as verbatim as possible without changing the meaning or duplicating info.
Only include info that is relevant to the TV show and ignore any irrelevant info.
There can be more than one TV show mentioned in the comments, so make sure to separate the info for each TV show.
Strip any season numbers, years and markdown from the TV show names. Always use the full name of the TV show if possible.
Do not add markdown, lists or extra newlines to the output. Output nothing if there is no relevant info.

Output syntax:
<TV show name>: <info>
"""

encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")


def count_tokens(text):
    return len(encoding.encode(text))


def cleanup_text(text):
    text = re.sub(r"\[.*?\]\(.*?\)", "", text)
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
    text = text.strip()
    return text


def extract_comment_data(text):
    text = text.strip()[:8192]

    n_input_tokens = count_tokens(text)
    print(f"Input tokens: {n_input_tokens}")

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": text},
        ],
        temperature=0.7,
        seed=random.randint(0, 100000),
    )

    n_output_tokens = count_tokens(response.choices[0].message.content)
    print(f"Output tokens: {n_output_tokens}")

    return response.choices[0].message.content


def main(args):
    if not os.path.exists(args.output_path):
        os.makedirs(args.output_path)

    print(f"Reading from {args.json_path}")

    submission = {}
    with open(args.json_path, "r") as f:
        submission = json.load(f)

    print(f"Found {len(submission['comments'])} comments")

    output_file = os.path.join(
        args.output_path,
        os.path.basename(args.json_path).replace(".json", ".txt"),
    )
    if os.path.exists(output_file):
        print(f"Skipping {args.json_path} because it was already processed")
        exit(0)

    threads = submission["comments"]

    with open(output_file, "w") as f:
        for thread in tqdm(threads, desc="Processing threads"):
            msg = cleanup_text(thread["body"])

            if msg.startswith("Shows from last week's"):
                continue

            for comment in thread["replies"]:
                msg += f"\n\t{cleanup_text(comment['body'])}"

            print(msg)

            extracted_data = extract_comment_data(msg).strip().split("\n")
            for line in extracted_data:
                line = line.strip()
                if line == "":
                    continue

                print(line)
                f.write(f"{line}\n")

            f.flush()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json_path", type=str, required=True)
    parser.add_argument("--output_path", type=str, required=True)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    main(args)
