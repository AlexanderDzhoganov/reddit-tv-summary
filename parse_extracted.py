import os
import argparse
import re
import json
import requests
import time
from dotenv import load_dotenv

load_dotenv()

pattern = r"(?P<show>[^:]+): (?P<info>.*)"


def find_show_id_by_name(show_name):
    show_name = show_name.strip().lower()
    shows_cache_file = os.path.join(os.path.dirname(__file__), "shows.json")

    shows_cache = None
    if os.path.exists(shows_cache_file):
        with open(shows_cache_file, "r") as f:
            shows_cache = json.load(f)

        if show_name in shows_cache["aliases"]:
            print(f"Cache hit for {show_name}: {shows_cache['aliases'][show_name]}")
            return shows_cache["aliases"][show_name]

    url = f"https://api.tvmaze.com/search/shows?q={show_name}"

    time.sleep(0.25)
    response = requests.get(url)
    data = response.json()

    if not data or len(data) == 0:
        print(f"Could not find show id for {show_name}")
        shows_cache["aliases"][show_name] = None
        with open(shows_cache_file, "w") as f:
            json.dump(shows_cache, f, indent=4)

        return None

    if shows_cache is None:
        shows_cache = {"aliases": {}, "shows": {}}

    sorted_shows = sorted(
        data,
        key=lambda x: (
            x["show"]["premiered"] if x["show"]["premiered"] else "0000-00-00"
        ),
        reverse=True,
    )
    show_data = sorted_shows[0]["show"]

    shows_cache["aliases"][show_name] = show_data["id"]
    shows_cache["shows"][show_data["id"]] = show_data

    print(f"Found show id for {show_name}: {show_data['id']}")

    with open(shows_cache_file, "w") as f:
        json.dump(shows_cache, f, indent=4)

    return show_data["id"]


def get_show_data(show_id):
    show_id = str(show_id)
    shows_cache_file = os.path.join(os.path.dirname(__file__), "shows.json")

    shows_cache = None
    if os.path.exists(shows_cache_file):
        with open(shows_cache_file, "r") as f:
            shows_cache = json.load(f)

        if show_id in shows_cache["shows"]:
            print(f"Cache hit for show id {show_id}")
            return shows_cache["shows"][show_id]

    print(f"Fetching show data for show id {show_id}")
    url = f"https://api.tvmaze.com/shows/{show_id}"
    response = requests.get(url)
    data = response.json()

    if shows_cache is None:
        shows_cache = {"aliases": {}, "shows": {}}

    shows_cache["shows"][show_id] = data

    with open(shows_cache_file, "w") as f:
        json.dump(shows_cache, f, indent=4)

    return data


def main(args):
    if not os.path.exists(os.path.dirname(args.output_path)):
        os.makedirs(os.path.dirname(args.output_path))

    txt = ""
    with open(args.input_path, "r") as f:
        txt += f.read()

    show_info = {}

    for line in txt.split("\n"):
        matches = re.finditer(pattern, line, re.DOTALL)
        for match in matches:
            show_name = match.group("show")
            info = match.group("info")

            show_id = find_show_id_by_name(show_name)
            if not show_id:
                print(f"Could not find show id for {show_name}")
                continue

            if show_id not in show_info:
                show_info[show_id] = []

            show_info[show_id].append(info)

    output_file = os.path.join(
        args.output_path, os.path.basename(args.input_path).split(".")[0] + ".json"
    )
    with open(output_file, "w") as f:
        json.dump(show_info, f, indent=4)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_path", type=str, required=True)
    parser.add_argument("--output_path", type=str, required=True)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    main(args)
