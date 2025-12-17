"""
Toronto Weekend Adventure Planner - Creates a comprehensive weekend adventure itinerary.

This skill analyzes the Toronto Guide databases and generates a structured itinerary page
with beach activities, cultural dining options, and coffee spots for a perfect weekend adventure.

The skill performs the following steps:
1. Finds the main Toronto Guide page
2. Discovers all child databases (Activities, Food, Cafes)
3. Queries each database with specific filters:
   - Activities: Filter for items with "Beaches" tag
   - Food: Filter for items with "Turkish" or "Hakka" tags
   - Cafes: Retrieve all entries
4. Creates a new "Perfect Weekend Adventure" page with:
   - Beach activities in a bulleted list with Google Maps links
   - Cultural dining in a numbered list with tags
   - Cafes in a toggle block with to-do items
   - Summary with counts
   - Divider and pro tip callout

Usage:
    python create_weekend_planner.py [--page-title "Toronto Guide"]
    
This is a general-purpose weekend planner that can be adapted for any city guide by
changing the page and database names.
"""

import os
import sys
import argparse
import logging
from typing import Dict, List, Optional, Any

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from skills.toronto_guide.utils import TorontoGuideNotionTools
from src.logger import get_logger

logger = get_logger(__name__)


class WeekendAdventurePlanner:
    """Create a comprehensive weekend adventure planner from city guide databases.
    
    This is a general-purpose weekend planner that can organize activities, dining,
    and coffee spots from any city guide database structure.
    """

    def __init__(
        self,
        api_key: str = None,
        main_page_name: str = "Toronto Guide",
        activities_db_name: str = "Activities",
        food_db_name: str = "Food",
        cafes_db_name: str = "Cafes",
        activities_tag: str = "Beaches",
        food_tags: List[str] = None,
    ):
        """
        Initialize WeekendAdventurePlanner.
        
        Args:
            api_key: Notion API key (defaults to EVAL_NOTION_API_KEY env var)
            main_page_name: Name of the main guide page (e.g., "Toronto Guide")
            activities_db_name: Name of the activities database
            food_db_name: Name of the food/restaurants database
            cafes_db_name: Name of the cafes database
            activities_tag: Tag to filter activities (default: "Beaches")
            food_tags: List of tags to filter restaurants (default: ["Turkish", "Hakka"])
        """
        if api_key is None:
            api_key = os.getenv("EVAL_NOTION_API_KEY")
        
        self.api_key = api_key
        self.tools = TorontoGuideNotionTools(api_key)
        self.main_page_name = main_page_name
        self.activities_db_name = activities_db_name
        self.food_db_name = food_db_name
        self.cafes_db_name = cafes_db_name
        self.activities_tag = activities_tag
        self.food_tags = food_tags or ["Turkish", "Hakka"]

    def create_planner(self) -> Dict[str, Any]:
        """
        Create the weekend adventure planner page.
        
        Returns:
            Dictionary with results including:
            - success: Boolean indicating overall success
            - page_id: ID of created page
            - data: Collected data (activities, restaurants, cafes)
            - errors: List of any errors encountered
        """
        result = {
            "success": False,
            "page_id": None,
            "data": {
                "beach_activities": [],
                "cultural_restaurants": [],
                "cafes": []
            },
            "errors": [],
            "debug_info": {}
        }

        try:
            # Step 1: Find the main guide page
            logger.info(f"Searching for main page: {self.main_page_name}")
            main_page_id = self.tools.search_page(self.main_page_name, "page")
            if not main_page_id:
                msg = f"Main page '{self.main_page_name}' not found"
                logger.error(msg)
                result["errors"].append(msg)
                return result
            
            result["debug_info"]["main_page_id"] = main_page_id
            logger.info(f"Found main page: {main_page_id}")

            # Step 2: Find databases
            logger.info("Searching for databases")
            databases = self.tools.find_databases_in_page(main_page_id)
            
            activities_db_id = None
            food_db_id = None
            cafes_db_id = None
            
            for db_name, db_id in databases.items():
                if self.activities_db_name in db_name:
                    activities_db_id = db_id
                    logger.info(f"Found Activities database: {db_id}")
                elif self.food_db_name in db_name:
                    food_db_id = db_id
                    logger.info(f"Found Food database: {db_id}")
                elif self.cafes_db_name in db_name:
                    cafes_db_id = db_id
                    logger.info(f"Found Cafes database: {db_id}")
            
            result["debug_info"]["databases"] = {
                "activities": activities_db_id,
                "food": food_db_id,
                "cafes": cafes_db_id
            }

            # Step 3: Query databases for data
            logger.info("Querying databases for data")
            
            # Query Activities
            if activities_db_id:
                beach_activities = self._query_activities(activities_db_id)
                result["data"]["beach_activities"] = beach_activities
                logger.info(f"Found {len(beach_activities)} beach activities")
            
            # Query Food
            if food_db_id:
                cultural_restaurants = self._query_restaurants(food_db_id)
                result["data"]["cultural_restaurants"] = cultural_restaurants
                logger.info(f"Found {len(cultural_restaurants)} cultural restaurants")
            
            # Query Cafes
            if cafes_db_id:
                cafes = self._query_cafes(cafes_db_id)
                result["data"]["cafes"] = cafes
                logger.info(f"Found {len(cafes)} cafes")

            # Step 4: Create the adventure page
            logger.info("Creating Perfect Weekend Adventure page")
            page_id = self.tools.create_page(main_page_id, "Perfect Weekend Adventure")
            if not page_id:
                msg = "Failed to create Perfect Weekend Adventure page"
                logger.error(msg)
                result["errors"].append(msg)
                return result
            
            result["page_id"] = page_id
            logger.info(f"Created page: {page_id}")

            # Step 5: Build and add blocks to the page
            logger.info("Building page content")
            blocks = self._build_page_blocks(
                result["data"]["beach_activities"],
                result["data"]["cultural_restaurants"],
                result["data"]["cafes"]
            )
            
            if not self.tools.add_blocks_to_page(page_id, blocks):
                msg = "Failed to add blocks to page"
                logger.error(msg)
                result["errors"].append(msg)
                return result
            
            logger.info(f"Added {len(blocks)} blocks to page")
            result["success"] = True
            return result

        except Exception as e:
            msg = f"Unexpected error in create_planner: {e}"
            logger.error(msg)
            result["errors"].append(msg)
            return result

    def _query_activities(self, db_id: str) -> List[Dict]:
        """Query activities database for items with specified tag."""
        activities = []
        try:
            filter_criteria = {
                "property": "Tags",
                "multi_select": {"contains": self.activities_tag}
            }
            pages = self.tools.query_database(db_id, filter_criteria)
            
            for page in pages:
                name = self.tools.get_page_property(page, "Name")
                url = self.tools.get_page_property(page, "Google Maps Link")
                if name:
                    activities.append({
                        "name": name,
                        "url": url or ""
                    })
            
            logger.info(f"Queried activities: found {len(activities)} with tag '{self.activities_tag}'")
            return activities
        except Exception as e:
            logger.error(f"Error querying activities: {e}")
            return []

    def _query_restaurants(self, db_id: str) -> List[Dict]:
        """Query food database for restaurants with specified tags."""
        restaurants = []
        try:
            # Build filter for multiple tags
            tag_filters = [
                {"property": "Tags", "multi_select": {"contains": tag}}
                for tag in self.food_tags
            ]
            filter_criteria = {"or": tag_filters}
            
            pages = self.tools.query_database(db_id, filter_criteria)
            
            seen_restaurants = set()
            for page in pages:
                name = self.tools.get_page_property(page, "Name")
                tags = self.tools.get_page_property(page, "Tags")
                
                if name and name not in seen_restaurants:
                    # Find which tag matches
                    matching_tag = None
                    if tags and isinstance(tags, list):
                        for tag in tags:
                            if tag in self.food_tags:
                                matching_tag = tag
                                break
                    
                    if matching_tag:
                        restaurants.append({
                            "name": name,
                            "tag": matching_tag
                        })
                        seen_restaurants.add(name)
            
            logger.info(f"Queried restaurants: found {len(restaurants)} with tags {self.food_tags}")
            return restaurants
        except Exception as e:
            logger.error(f"Error querying restaurants: {e}")
            return []

    def _query_cafes(self, db_id: str) -> List[str]:
        """Query cafes database for all cafes."""
        cafes = []
        try:
            pages = self.tools.query_database(db_id)
            
            for page in pages:
                name = self.tools.get_page_property(page, "Name")
                if name:
                    cafes.append(name)
            
            logger.info(f"Queried cafes: found {len(cafes)}")
            return cafes
        except Exception as e:
            logger.error(f"Error querying cafes: {e}")
            return []

    def _build_page_blocks(
        self,
        beach_activities: List[Dict],
        restaurants: List[Dict],
        cafes: List[str]
    ) -> List[Dict]:
        """Build all the blocks for the weekend adventure page."""
        blocks = []
        
        # Title
        blocks.append({
            "type": "heading_1",
            "heading_1": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": "🎒 Perfect Weekend Adventure"}
                    }
                ]
            }
        })
        
        # Beach Activities section
        blocks.append({
            "type": "heading_2",
            "heading_2": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": "🏖️ Beach Activities"}
                    }
                ]
            }
        })
        
        for activity in beach_activities:
            activity_text = activity["name"]
            if activity["url"]:
                activity_text += f" - {activity['url']}"
            
            blocks.append({
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": activity_text}
                        }
                    ]
                }
            })
        
        # Cultural Dining section
        blocks.append({
            "type": "heading_2",
            "heading_2": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": "🍽️ Cultural Dining Experience"}
                    }
                ]
            }
        })
        
        for restaurant in restaurants:
            restaurant_text = f"{restaurant['name']} (Tag: {restaurant['tag']})"
            blocks.append({
                "type": "numbered_list_item",
                "numbered_list_item": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": restaurant_text}
                        }
                    ]
                }
            })
        
        # Coffee Break Spots section
        blocks.append({
            "type": "heading_2",
            "heading_2": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": "☕ Coffee Break Spots"}
                    }
                ]
            }
        })
        
        # Toggle with cafes as to-do items
        cafe_children = []
        for cafe in cafes:
            cafe_children.append({
                "type": "to_do",
                "to_do": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": cafe}
                        }
                    ],
                    "checked": False
                }
            })
        
        blocks.append({
            "type": "toggle",
            "toggle": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": "Top Cafes to Visit"}
                    }
                ],
                "children": cafe_children
            }
        })
        
        # Weekend Summary section
        blocks.append({
            "type": "heading_2",
            "heading_2": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": "📊 Weekend Summary"}
                    }
                ]
            }
        })
        
        summary_text = f"This weekend includes {len(beach_activities)} beach activities, {len(restaurants)} cultural dining options, and {len(cafes)} coffee spots to explore!"
        blocks.append({
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": summary_text}
                    }
                ]
            }
        })
        
        # Divider
        blocks.append({
            "type": "divider",
            "divider": {}
        })
        
        # Callout with pro tip
        blocks.append({
            "type": "callout",
            "callout": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": "Pro tip: Check the Seasons database for the best time to enjoy outdoor activities!"}
                    }
                ],
                "icon": {
                    "type": "emoji",
                    "emoji": "💡"
                }
            }
        })
        
        return blocks


def main():
    """Main entry point with argparse CLI."""
    parser = argparse.ArgumentParser(
        description="Create a comprehensive weekend adventure planner from city guide databases"
    )
    
    parser.add_argument(
        "--main-page",
        default="Toronto Guide",
        help="Name of the main guide page (default: 'Toronto Guide')"
    )
    
    parser.add_argument(
        "--activities-db",
        default="Activities",
        help="Name of the activities database (default: 'Activities')"
    )
    
    parser.add_argument(
        "--food-db",
        default="Food",
        help="Name of the food database (default: 'Food')"
    )
    
    parser.add_argument(
        "--cafes-db",
        default="Cafes",
        help="Name of the cafes database (default: 'Cafes')"
    )
    
    parser.add_argument(
        "--activities-tag",
        default="Beaches",
        help="Tag to filter activities (default: 'Beaches')"
    )
    
    parser.add_argument(
        "--food-tags",
        nargs="+",
        default=["Turkish", "Hakka"],
        help="Tags to filter restaurants (default: 'Turkish' 'Hakka')"
    )

    args = parser.parse_args()

    logger.info("Starting weekend adventure planner with parameters:")
    logger.info(f"  Main page: {args.main_page}")
    logger.info(f"  Activities DB: {args.activities_db}")
    logger.info(f"  Food DB: {args.food_db}")
    logger.info(f"  Cafes DB: {args.cafes_db}")
    logger.info(f"  Activities tag: {args.activities_tag}")
    logger.info(f"  Food tags: {args.food_tags}")

    # Create planner and execute
    planner = WeekendAdventurePlanner(
        main_page_name=args.main_page,
        activities_db_name=args.activities_db,
        food_db_name=args.food_db,
        cafes_db_name=args.cafes_db,
        activities_tag=args.activities_tag,
        food_tags=args.food_tags
    )

    result = planner.create_planner()

    # Output results
    print("\n" + "=" * 70)
    print("WEEKEND ADVENTURE PLANNER RESULTS")
    print("=" * 70)
    print(f"Success: {result['success']}")
    if result['page_id']:
        print(f"Page ID: {result['page_id']}")
    
    print(f"\nData collected:")
    print(f"  Beach activities: {len(result['data']['beach_activities'])}")
    for activity in result['data']['beach_activities']:
        url_info = f" - {activity['url']}" if activity['url'] else ""
        print(f"    - {activity['name']}{url_info}")
    
    print(f"\n  Cultural restaurants: {len(result['data']['cultural_restaurants'])}")
    for restaurant in result['data']['cultural_restaurants']:
        print(f"    - {restaurant['name']} (Tag: {restaurant['tag']})")
    
    print(f"\n  Cafes: {len(result['data']['cafes'])}")
    for cafe in result['data']['cafes']:
        print(f"    - {cafe}")
    
    if result["errors"]:
        print("\nErrors encountered:")
        for error in result["errors"]:
            print(f"  ✗ {error}")
    
    print("=" * 70)

    # Exit with appropriate code
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
