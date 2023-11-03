import json
import os

import requests
from notion_client import Client

from common import list_art_by_filter


def search_databases(notion: Client, query: str = None) -> dict:
    return notion.search(
        query=query,
        filter={
            "value": "database",
            "property": "object",
        }
    )


def list_options_for_property(db_resp: dict, property_name: str) -> list[dict]:
    return db_resp["properties"][property_name]["multi_select"]["options"]


def list_options_character_owners(db_resp: dict) -> list[dict]:
    return list_options_for_property(db_resp, "Character owners")


def list_options_posted_to(db_resp: dict) -> list[dict]:
    return list_options_for_property(db_resp, "Posted to")


def list_spangle_to_post(notion: Client, db_resp: dict) -> list[dict]:
    return list_art_to_post(notion, db_resp, ["Spangle FA", "Spangle not posting"], ["Spangle"])


def list_art_to_post(notion: Client, db_resp: dict, posted_to: list[str], character_owners: list[str]) -> list[dict]:
    card_filter = {
        "and": [
            *[
                {
                    "property": "Posted to",
                    "multi_select": {
                        "does_not_contain": gallery,
                    },
                }
                for gallery in posted_to
            ],
            *[
                {
                    "property": "Character owners",
                    "multi_select": {
                        "contains": character,
                    },
                }
                for character in character_owners
            ],
            {
                "property": "Progress",
                "select": {
                    "equals": "Complete",
                },
            },
        ]
    }
    return list_art_by_filter(notion, db_resp, card_filter)


def download_post(post: dict, folder: str) -> None:
    print(f"Downloading post: {post['id']}")
    title = post["properties"]["Name"]["title"][0]["text"]["content"]
    print(f"Title: {title}")
    link = post["url"]
    print(f"Link: {link}")
    artists = [artist["name"] for artist in post["properties"]["Artist"]["multi_select"]]
    artists_str = " and ".join(artists)
    print(f"Artist(s): {artists_str}")
    final_files = post["properties"]["Final"]["files"]
    print(f"File count: {len(final_files)}")
    post_folder = f"{folder}/{title} by {artists_str}"
    os.makedirs(post_folder, exist_ok=True)
    with open(f"{post_folder}/link.txt", "w") as f:
        f.write(link)
    filenames = []
    for final_file in final_files:
        filename = final_file["name"]
        n = 0
        while filename in filenames:
            n += 1
            filename_split = filename.rsplit(".", 1)
            filename = f"{filename_split[0]}.{n}"
            if len(filename_split) > 1:
                filename = f".{filename_split[1]}"
        filenames.append(filename)
        local_filename = f"{post_folder}/{filename}"
        if os.path.exists(local_filename):
            print(f"Skipping dl of existing file: {filename}")
            continue
        print(f"Downloading: {filename}")
        url = final_file["file"]["url"]
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
    print("-----")


def download_posts(posts: list[dict], folder: str) -> None:
    os.makedirs(folder, exist_ok=True)
    for post in posts:
        download_post(post, folder)


def download_art_to_post(notion: Client, art_db_resp: dict, gallery: str) -> None:
    if gallery not in ["Spangle", "Zephyr", "e621"]:
        raise ValueError("Invalid gallery option.")
    not_posted_to = {
        "Spangle": ["Spangle FA", "Spangle not posting"],
        "Zephyr": ["Zephyr FA", "Zephyr not posting"],
        "e621": ["e621"],
    }[gallery]
    character_owners = {
        "Spangle": ["Spangle"],
        "Zephyr": ["Zephyr"],
        "e621": ["Spangle", "Zephyr"],
    }[gallery]
    folder = {
        "Spangle": "Art to post/Spangle",
        "Zephyr": "Art to post/Zephyr",
        "e621": "Art to post/e621",
    }[gallery]
    art_to_post = list_art_to_post(notion, art_db_resp, not_posted_to, character_owners)
    print(f"Found {len(art_to_post)} arts which need posting.")
    download_posts(art_to_post, folder)


def main(config: dict) -> None:
    notion = Client(auth=config["notion"]["integration_secret"])
    art_db_resp = notion.databases.retrieve(config["notion"]["art_db_id"])
    download_art_to_post(notion, art_db_resp, "Zephyr")
    print("---")


if __name__ == '__main__':
    with open("config.json", "r") as fc:
        c = json.load(fc)
    main(c)
