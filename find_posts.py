import os
import argparse
import praw
import json
from dotenv import load_dotenv

load_dotenv()

reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT"),
)


def main(args):
    if not os.path.exists(args.output_path):
        os.makedirs(args.output_path)

    # https://old.reddit.com/r/television/search?q=flair%3A%22Weekly+Rec+Thread%22&restrict_sr=on&sort=new&t=all
    subreddit = reddit.subreddit("television")

    posts = {}
    output_file = os.path.join(args.output_path, "posts.json")

    if os.path.exists(output_file):
        with open(output_file, "r") as f:
            posts = json.load(f)

    for submission in subreddit.search(
        query='flair:"Weekly Rec Thread"',
        sort="new",
        time_filter=args.time_filter,
        limit=args.limit,
    ):
        if submission.id in posts:
            print(f"Skipping {submission.id} because it was already added")
            continue

        # if not posted by AutoModerator, skip
        if submission.author != "AutoModerator":
            print(
                f"Skipping {submission.id} because it was not posted by AutoModerator"
            )
            continue

        posts[submission.id] = {
            "title": submission.title,
            "selftext": submission.selftext,
            "url": submission.url,
            "created_utc": submission.created_utc,
        }
        print(f"Added {submission.id}")

    with open(output_file, "w") as f:
        json.dump(posts, f, indent=4)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output_path", type=str, required=True)
    parser.add_argument(
        "--time_filter",
        type=str,
        default="week",
        choices=["hour", "day", "week", "month", "year", "all"],
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    main(args)
