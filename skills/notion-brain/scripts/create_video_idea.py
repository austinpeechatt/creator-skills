#!/usr/bin/env python3
"""
Creates a YouTube Video Idea page in your Notion database.
Reads structured JSON from a file path passed as argv[1].
"""

import json
import sys
import os
import urllib.request
import urllib.error

NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
DATABASE_ID = os.environ.get("NOTION_YOUTUBE_DB_ID")  # see .env.example
NOTION_VERSION = "2022-06-28"

def notion_request(method, endpoint, data=None):
    url = f"https://api.notion.com/v1/{endpoint}"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"ERROR: Notion API {e.code} — {error_body}", file=sys.stderr)
        sys.exit(1)


def text_block(content):
    return {"text": {"content": content}}


def heading2(text):
    return {
        "object": "block",
        "type": "heading_2",
        "heading_2": {"rich_text": [text_block(text)]},
    }


def heading3(text):
    return {
        "object": "block",
        "type": "heading_3",
        "heading_3": {"rich_text": [text_block(text)]},
    }


def bullet(text):
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": [text_block(text)]},
    }


def paragraph(text):
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": [text_block(text)]},
    }


def divider():
    return {"object": "block", "type": "divider", "divider": {}}


def build_children(sections):
    """
    Converts a list of section dicts into Notion blocks.
    Each section: {"heading": str, "type": "bullets"|"paragraphs"|"sub_sections", "content": [...]}
    Sub-sections: {"heading": str, "type": "bullets"|"paragraphs", "content": [...]}
    """
    children = []
    for section in sections:
        children.append(heading2(section["heading"]))

        if section["type"] == "sub_sections":
            for sub in section["content"]:
                children.append(heading3(sub["heading"]))
                for item in sub.get("content", []):
                    children.append(bullet(item))
        elif section["type"] == "bullets":
            for item in section["content"]:
                children.append(bullet(item))
        elif section["type"] == "paragraphs":
            for item in section["content"]:
                children.append(paragraph(item))
        elif section["type"] == "mixed":
            for item in section["content"]:
                if isinstance(item, dict):
                    if item.get("type") == "heading3":
                        children.append(heading3(item["text"]))
                    elif item.get("type") == "paragraph":
                        children.append(paragraph(item["text"]))
                    elif item.get("type") == "bullet":
                        children.append(bullet(item["text"]))
                    elif item.get("type") == "divider":
                        children.append(divider())
                else:
                    children.append(bullet(item))

        children.append(divider())

    return children


def main():
    if not NOTION_API_KEY:
        print("ERROR: NOTION_API_KEY not set in environment", file=sys.stderr)
        sys.exit(1)

    if len(sys.argv) < 2:
        print("ERROR: Pass the JSON file path as an argument", file=sys.stderr)
        sys.exit(1)

    with open(sys.argv[1]) as f:
        data = json.load(f)

    # Required fields
    title = data["title"]
    difficulty = data.get("difficulty", "Medium")
    tags = data.get("tags", [])
    status = data.get("status", "Not started")
    form = data.get("form", "Long")
    sections = data.get("sections", [])

    # Build properties
    properties = {
        "Video Idea": {"title": [text_block(title)]},
        "Difficulty": {"select": {"name": difficulty}},
        "Tags": {"multi_select": [{"name": t} for t in tags]},
        "Status": {"status": {"name": status}},
        "Form": {"select": {"name": form}},
    }

    # Build page content
    children = build_children(sections) if sections else []

    payload = {
        "parent": {"database_id": DATABASE_ID},
        "properties": properties,
    }
    if children:
        payload["children"] = children

    result = notion_request("POST", "pages", payload)

    page_title = result["properties"]["Video Idea"]["title"][0]["plain_text"]
    page_url = result["url"]
    print(f"SUCCESS: {page_title}")
    print(f"URL: {page_url}")


if __name__ == "__main__":
    main()
