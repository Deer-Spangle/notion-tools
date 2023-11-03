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


def list_all_cards(notion: Client, db_resp: dict) -> list[dict]:
    return list_art_by_filter(notion, db_resp, None)


def validate_character_owners(all_cards: list[dict]) -> None:
    owners_characters = {
        "Spangle": ["Deer-Spangle", "Doe-Spangle", "Samariah", "Feral-Spangle", "Dragon Spangle", "Kobold-Spangle", "Hallo", "Dawn (Umbreon)"],
        "Zephyr": ["Zephyr", "Zephyr's brother", "Zephyr-burd", "Zephling", "Zephkitty"],
        "Ink": ["Inky"],
        "Generic": ["Generic", "ych", "Dragonair"],
        "NPC": ["Isabelle", "Demon core", "Toothless", "Lightfury"],
    }
    other_owner = "Other"
    # Validate no owner overlaps
    all_known_characters = [char for chars in owners_characters.values() for char in chars]
    assert len(all_known_characters) == len(set(all_known_characters)), "Character is assigned to more than one owner"

    # Define a lookup function
    def owner_for_character(character: str) -> str:
        for owner, chars in owners_characters.items():
            if character in chars:
                return owner
        return other_owner

    for card in all_cards:
        card_link = card["url"]
        characters = [character["name"] for character in card["properties"]["Characters"]["multi_select"]]
        owners = [owner["name"] for owner in card["properties"]["Character owners"]["multi_select"]]
        correct_owners = set()
        for character in characters:
            owner = owner_for_character(character)
            correct_owners.add(owner)
        if set(correct_owners) != set(owners):
            print(f"INVALID: Owners for card should be {correct_owners} in card: {card_link}")


def main(config: dict) -> None:
    notion = Client(auth=config["notion"]["integration_secret"])
    art_db_resp = notion.databases.retrieve(config["notion"]["art_db_id"])
    all_art = list_all_cards(notion, art_db_resp)
    print(f"There are {len(all_art)} total art cards")
    # Check that characters and character owners line up
    validate_character_owners(all_art)
    # TODO: Check that completed has final
    # TODO: Check that incomplete does not have final
    # TODO: Check that artist is set
    # TODO: Check that titles are unique
    print("---")


if __name__ == '__main__':
    with open("config.json", "r") as fc:
        c = json.load(fc)
    main(c)
