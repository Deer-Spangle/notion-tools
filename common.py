from typing import Optional

from notion_client import Client


def list_art_by_filter(notion: Client, db_resp: dict, card_filter: Optional[dict]) -> list[dict]:
    next_token = None
    results = []
    while True:
        print("Fetching a page of art results")
        resp = notion.databases.query(
            db_resp["id"],
            start_cursor=next_token,
            filter=card_filter
        )
        results += resp["results"]
        next_token = resp.get("next_cursor")
        if next_token is None:
            return results
