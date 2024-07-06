import os
import argparse
import json
from dotenv import load_dotenv
from openai import OpenAI
import tiktoken
import random
import re
from tqdm import tqdm
from parse_extracted import get_show_data

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

system_message = """
You are a TV show reviewer and you are given a list of comments about a specific TV show.
Create a humorous and mocking summary in the style of n-gate.com.
It should be 3-4 sentences, and mock both the show and the commenters.
Use emojis and Reddit markdown for emphasis. Make it SHORT and BITING.
Summarize the comments into a single paragraph. Comment on the difference between this week's and last week's comments.
"""

encoding = tiktoken.encoding_for_model("gpt-4o")


def count_tokens(text):
    return len(encoding.encode(text))


def cleanup_text(text):
    text = re.sub(r"\[.*?\]\(.*?\)", "", text)
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
    text = text.strip()
    return text


def summarize(text):
    text = text.strip()[:8192]

    n_input_tokens = count_tokens(text)
    print(f"Input tokens: {n_input_tokens}")

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": text},
        ],
        temperature=0.8,
        seed=random.randint(0, 100000),
    )

    n_output_tokens = count_tokens(response.choices[0].message.content)
    print(f"Output tokens: {n_output_tokens}")

    return response.choices[0].message.content


def main(args):
    if not os.path.exists(os.path.dirname(args.output_path)):
        os.makedirs(os.path.dirname(args.output_path))

    prev_json = {}
    with open(args.prev_json, "r") as f:
        prev_json = json.load(f)

    cur_json = {}
    with open(args.cur_json, "r") as f:
        cur_json = json.load(f)

    comment_counts = {}
    for show_id, data in prev_json.items():
        comment_counts[show_id] = len(data)

    for show_id, data in cur_json.items():
        if show_id not in comment_counts:
            comment_counts[show_id] = 0
        comment_counts[show_id] += len(data)

    sorted_shows = sorted(comment_counts.items(), key=lambda x: x[1], reverse=True)[
        : args.topk
    ]

    for show_id, _ in tqdm(sorted_shows):
        output_file = os.path.join(args.output_path, f"{show_id}.txt")
        if os.path.exists(output_file):
            continue

        show_data = get_show_data(show_id)
        print(show_data["name"], show_data["id"])

        prev_comments = []
        if show_id in prev_json:
            prev_comments = [cleanup_text(comment) for comment in prev_json[show_id]]
            prev_comments = prev_comments[:20]

        cur_comments = []

        if show_id in cur_json:
            cur_comments = [cleanup_text(comment) for comment in cur_json[show_id]]
            cur_comments = cur_comments[:20]

        text = "Show: " + show_data["name"] + "\n"
        text += "Summary: " + show_data["summary"] + "\n"
        text += "Previous week comments:\n"
        text += "\n".join(prev_comments)
        text += "\n\nCurrent week comments:\n"
        text += "\n".join(cur_comments)

        summary = summarize(text)
        print(summary)

        with open(output_file, "w") as f:
            f.write(summary)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prev_json", type=str, required=True)
    parser.add_argument("--cur_json", type=str, required=True)
    parser.add_argument("--output_path", type=str, required=True)
    parser.add_argument("--topk", type=int, default=10)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    main(args)
