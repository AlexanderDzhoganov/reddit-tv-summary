import os
import argparse
import praw
import json
import datetime
from tqdm import tqdm
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

    posts = {}
    with open(args.json_path, "r") as f:
        posts = json.load(f)

    sorted_posts = sorted(
        posts.items(), key=lambda x: x[1]["created_utc"], reverse=True
    )

    for post_id, post in tqdm(sorted_posts, desc="Processing posts"):
        print(f"Processing {post_id}")

        submission_time = datetime.datetime.fromtimestamp(post["created_utc"])
        filename = submission_time.strftime("%Y%m%d") + ".json"

        if os.path.exists(os.path.join(args.output_path, filename)):
            print(f"Skipping {post_id} because it was already processed")
            continue

        submission = reddit.submission(url=post["url"])
        submission.comments.replace_more(limit=None)

        comments = []
        for comment in submission.comments:
            comments.append(
                {
                    "body": comment.body,
                    "created_utc": comment.created_utc,
                    "replies": [
                        {
                            "body": reply.body,
                            "created_utc": reply.created_utc,
                        }
                        for reply in comment.replies
                    ],
                }
            )

        print(f"Found {len(comments)} comments")

        with open(os.path.join(args.output_path, filename), "w") as f:
            json.dump(
                {
                    "title": submission.title,
                    "selftext": submission.selftext,
                    "comments": comments,
                },
                f,
                indent=4,
            )


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json_path", type=str, required=True)
    parser.add_argument("--output_path", type=str, required=True)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    main(args)
