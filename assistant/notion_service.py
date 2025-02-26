import os
import requests
import time
from dotenv import load_dotenv


class NotionParser:
    def __init__(self, api_key, page_id):
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }
        self.root_page_id = page_id

    def get_page_blocks(self, page_id):
        """
        Fetch all blocks (content) from a Notion page.
        """
        url = f"https://api.notion.com/v1/blocks/{page_id}/children"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching page {page_id}: {response.status_code}, {response.text}")
            return None

    def parse_blocks(self, blocks, company_name="", current_page_id=None):
        content = []
        child_pages = []

        for block in blocks.get("results", []):
            block_type = block["type"]

            if block_type in ["heading_1", "heading_2", "heading_3"]:
                text = block[block_type]["rich_text"]
                if text:
                    heading_level = int(block_type[-1])
                    content.append(("#" * heading_level) + " " + text[0]["plain_text"])

            elif block_type == "paragraph":
                text = block["paragraph"]["rich_text"]
                if text:
                    content.append(text[0]["plain_text"])

            elif block_type == "bulleted_list_item":
                text = block["bulleted_list_item"]["rich_text"]
                if text:
                    content.append(f"- {text[0]['plain_text']}")

            elif block_type == "child_page":
                child_page_id = block["id"]
                child_company_name = block["child_page"]["title"]
                print(f"Fetching child page: {child_company_name} ({child_page_id})")

                # Recursively fetch child pages
                child_content = self.fetch_page_recursively(child_page_id, child_company_name)
                child_pages.extend(child_content)

            time.sleep(0.2)

        # If the root page is empty, return only child pages
        if not content and not company_name:
            return child_pages  # Skip empty root pages

        result = {
            "company_name": company_name,
            "prompt_text": "\n\n".join(content),
        }

        if company_name and current_page_id:
            result[
                "prompt_url"] = f"https://www.notion.so/{company_name.replace(' ', '-').lower()}-{current_page_id.replace('-', '')}"
        else:
            result["prompt_url"] = f"https://www.notion.so/{self.root_page_id.replace('-', '')}"

        return [result] + child_pages

    def fetch_page_recursively(self, page_id, company_name=""):
        """
        Recursively fetch and parse Notion pages, including child pages.
        Returns structured data as a list of dictionaries.
        """
        blocks = self.get_page_blocks(page_id)
        if not blocks:
            return []

        parsed_data = self.parse_blocks(blocks, company_name, page_id if company_name else None)

        return parsed_data



