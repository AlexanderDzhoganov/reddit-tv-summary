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
You are a TV show reviewer and you are given a list of comments about a specific TV show.
Create a humorous and mocking summary in the style of n-gate.com.
It should be 3-4 sentences, and mock both the article and the commenters.
Use emojis or Reddit markdown for emphasis. Make it SHORT and BITING.
Do not include the name of the TV show or any headings, just the summary.
Summarize the comments into a single paragraph. Do not include any spoilers or irrelevant information.
"""

encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")


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
    if not os.path.exists(os.path.dirname(args.output_path)):
        os.makedirs(os.path.dirname(args.output_path))

    print(f"Reading from {args.json_path}")

    parsed_comments = {}
    with open(args.json_path, "r") as f:
        parsed_comments = json.load(f)

    print(f"Found data for {len(parsed_comments)} shows")

    sorted_shows = sorted(
        parsed_comments.items(), key=lambda x: len(x[1]["info"]), reverse=True
    )
    sorted_shows = sorted_shows[: args.topk]

    print(f"Summarizing info for top {args.topk} shows")

    for show_id, data in tqdm(sorted_shows):
        print(data["show"]["name"], data["show"]["id"])

        text = "Show: " + data["show"]["name"] + "\n"
        text += "Summary: " + data["show"]["summary"] + "\n"
        text += "User comments:\n"
        text += "\n".join(data["info"])

        summary = summarize(text)
        print(summary)

        output_file = os.path.join(args.output_path, f"{show_id}.txt")
        with open(output_file, "w") as f:
            f.write(summary)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json_path", type=str, required=True)
    parser.add_argument("--output_path", type=str, required=True)
    parser.add_argument("--topk", type=int, default=10)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    main(args)
