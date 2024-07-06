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

    submission = reddit.submission(id=args.thread_id)
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

    with open(os.path.join(args.output_path, f"{args.thread_id}.json"), "w") as f:
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
    parser.add_argument("--thread_id", type=str, required=True)
    parser.add_argument("--output_path", type=str, required=True)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    main(args)
