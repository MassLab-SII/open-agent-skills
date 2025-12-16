"""
Travel Itinerary Filter - Removes itinerary items from a travel database based on configurable criteria.

This skill removes itinerary entries from a travel database based on:
- Location/Group filter
- Day filter  
- Time threshold filter (after/before a specified time)

The skill can be parameterized to handle various travel planning scenarios by adjusting
location, days, and time cutoffs through command-line arguments.

Usage:
    python remove_osaka_itinerary.py remove [OPTIONS]
    
This is a general-purpose travel itinerary filtering tool that can be adapted for any
location, day combination, and time threshold by changing parameters.
"""

import os
import sys
import argparse
import logging
from typing import Dict, List, Optional

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from skills.japan_travel_planner.utils import TravelNotionTools
from src.logger import get_logger

logger = get_logger(__name__)


class TravelItineraryFilter:
    """Filter and remove travel itinerary items based on configurable criteria.
    
    This is a general-purpose itinerary filtering tool that can remove items based on:
    - Location/Group filter (e.g., Osaka, Tokyo, Kyoto)
    - Day filter (e.g., Day 1, Day 2, specific dates)
    - Time threshold (e.g., after 6 PM, before 3 PM)
    
    The same skill can be used for different locations, days, and time thresholds
    by simply changing the parameters.
    """

    def __init__(
        self,
        api_key: str = None,
        hub_page_name: str = "Japan Travel Planner",
        database_name: str = "Travel Itinerary",
        location: str = "Osaka",
        days: List[str] = None,
        cutoff_time_minutes: int = 18 * 60,  # 6 PM in minutes
    ):
        """
        Initialize TravelItineraryFilter.
        
        Args:
            api_key: Notion API key (defaults to EVAL_NOTION_API_KEY env var)
            hub_page_name: Name of the hub page containing the itinerary
            database_name: Name of the itinerary database
            location: Location/Group to filter (e.g., "Osaka", "Tokyo")
            days: List of days to process (e.g., ["Day 1", "Day 2"])
            cutoff_time_minutes: Time threshold in minutes (e.g., 1080 for 6 PM)
        """
        if api_key is None:
            api_key = os.getenv("EVAL_NOTION_API_KEY")
        
        self.api_key = api_key
        self.tools = TravelNotionTools(api_key)
        self.hub_page_name = hub_page_name
        self.database_name = database_name
        self.location = location
        self.days = days or ["Day 1", "Day 2"]
        self.cutoff_time_minutes = cutoff_time_minutes

    def remove_itinerary(self) -> Dict[str, any]:
        """
        Remove itinerary items from the specified location after the cutoff time.
        
        Returns:
            Dictionary with results including:
            - success: Boolean indicating overall success
            - removed_count: Number of items removed
            - removed_items: List of removed item details
            - errors: List of any errors encountered
        """
        result = {
            "success": False,
            "removed_count": 0,
            "removed_items": [],
            "errors": [],
            "debug_info": {}
        }

        try:
            # Step 1: Find the hub page
            logger.info(f"Searching for hub page: {self.hub_page_name}")
            hub_page_id = self.tools.search_page(self.hub_page_name, "page")
            if not hub_page_id:
                msg = f"Hub page '{self.hub_page_name}' not found"
                logger.error(msg)
                result["errors"].append(msg)
                return result
            
            result["debug_info"]["hub_page_id"] = hub_page_id
            logger.info(f"Found hub page: {hub_page_id}")

            # Step 2: Find the travel itinerary database
            logger.info(f"Searching for database: {self.database_name}")
            db_id = self.tools.find_database_in_children(hub_page_id, self.database_name)
            if not db_id:
                msg = f"Database '{self.database_name}' not found in {self.hub_page_name}"
                logger.error(msg)
                result["errors"].append(msg)
                return result
            
            result["debug_info"]["database_id"] = db_id
            logger.info(f"Found database: {db_id}")

            # Step 3: Build filter for location and days (case-insensitive)
            # First, try exact match
            filter_criteria = {
                "and": [
                    {
                        "property": "Group",
                        "select": {"equals": self.location}
                    },
                    {
                        "or": [
                            {"property": "Day", "select": {"equals": day}}
                            for day in self.days
                        ]
                    }
                ]
            }

            logger.info(f"Querying database for {self.location} items on {self.days}")
            pages = self.tools.query_database_with_filter(db_id, filter_criteria)
            
            # If no results with exact match, try case-insensitive match by fetching all and filtering
            if not pages:
                logger.info(f"No exact match for location '{self.location}', trying case-insensitive search")
                # Get all items for the specified days
                days_filter = {
                    "or": [
                        {"property": "Day", "select": {"equals": day}}
                        for day in self.days
                    ]
                }
                all_pages = self.tools.query_database_with_filter(db_id, days_filter)
                # Filter client-side by location (case-insensitive)
                pages = [p for p in all_pages if self.tools.get_page_property(p, "Group", "").lower() == self.location.lower()]
                logger.info(f"Found {len(pages)} items with case-insensitive location match")
            
            result["debug_info"]["total_queried"] = len(pages)
            logger.info(f"Found {len(pages)} items matching criteria")

            # Step 4: Filter items by time
            items_to_remove = []
            for page in pages:
                page_id = page.get("id")
                page_title = self.tools.get_page_property(page, "Name")
                page_time = self.tools.get_page_property(page, "Notes")
                page_day = self.tools.get_page_property(page, "Day")
                page_group = self.tools.get_page_property(page, "Group")

                # Double-check group match (case-insensitive)
                if page_group.lower() != self.location.lower():
                    continue

                # Parse time
                time_minutes = self.tools.parse_time_to_minutes(page_time)
                
                logger.debug(f"Item: {page_title}, Time: {page_time} ({time_minutes} min), Day: {page_day}")

                # Check if after cutoff time (strictly greater than, not equal)
                if time_minutes is not None and time_minutes > self.cutoff_time_minutes:
                    items_to_remove.append({
                        "page_id": page_id,
                        "title": page_title,
                        "time": page_time,
                        "day": page_day,
                        "time_minutes": time_minutes
                    })
                    logger.info(f"Will remove: {page_title} at {page_time} on {page_day}")

            result["debug_info"]["items_to_remove_count"] = len(items_to_remove)

            # Step 5: Remove the items
            for item in items_to_remove:
                try:
                    success = self.tools.archive_page(item["page_id"])
                    if success:
                        result["removed_items"].append(item)
                        result["removed_count"] += 1
                        logger.info(f"Successfully removed: {item['title']}")
                    else:
                        msg = f"Failed to remove: {item['title']}"
                        logger.error(msg)
                        result["errors"].append(msg)
                except Exception as e:
                    msg = f"Error removing {item['title']}: {e}"
                    logger.error(msg)
                    result["errors"].append(msg)

            result["success"] = len(result["errors"]) == 0
            return result

        except Exception as e:
            msg = f"Unexpected error in remove_itinerary: {e}"
            logger.error(msg)
            result["errors"].append(msg)
            return result


def main():
    """Main entry point with argparse CLI."""
    parser = argparse.ArgumentParser(
        description="Filter and remove travel itinerary items based on location, day, and time criteria"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Main 'remove' command (default behavior)
    remove_parser = subparsers.add_parser(
        "remove",
        help="Filter and remove itinerary items"
    )
    
    remove_parser.add_argument(
        "--hub-page",
        default="Japan Travel Planner",
        help="Name of the hub page (default: 'Japan Travel Planner')"
    )
    
    remove_parser.add_argument(
        "--database-name",
        default="Travel Itinerary",
        help="Name of the itinerary database (default: 'Travel Itinerary')"
    )
    
    remove_parser.add_argument(
        "--location",
        default="Osaka",
        help="Location/Group to filter (default: 'Osaka')"
    )
    
    remove_parser.add_argument(
        "--days",
        nargs="+",
        default=["Day 1", "Day 2"],
        help="Days to process (default: 'Day 1' 'Day 2')"
    )
    
    remove_parser.add_argument(
        "--cutoff-time",
        type=int,
        default=18,
        help="Cutoff time in 24-hour format (default: 18 for 6 PM)"
    )
    
    # Also support 'audit' as an alias for backward compatibility
    audit_parser = subparsers.add_parser(
        "audit",
        help="Run filtering with audit configuration"
    )
    
    audit_parser.add_argument(
        "--hub-page",
        default="Japan Travel Planner",
        help="Name of the hub page (default: 'Japan Travel Planner')"
    )
    
    audit_parser.add_argument(
        "--database-name",
        default="Travel Itinerary",
        help="Name of the itinerary database (default: 'Travel Itinerary')"
    )
    
    audit_parser.add_argument(
        "--location",
        default="Osaka",
        help="Location/Group to filter (default: 'Osaka')"
    )
    
    audit_parser.add_argument(
        "--days",
        nargs="+",
        default=["Day 1", "Day 2"],
        help="Days to process (default: 'Day 1' 'Day 2')"
    )
    
    audit_parser.add_argument(
        "--cutoff-time",
        type=int,
        default=18,
        help="Cutoff time in 24-hour format (default: 18 for 6 PM)"
    )

    # Parse arguments
    args = parser.parse_args()
    
    # Default to 'remove' if no command specified
    command = args.command or "remove"
    
    # Extract parameters
    hub_page = getattr(args, "hub_page", "Japan Travel Planner")
    database_name = getattr(args, "database_name", "Travel Itinerary")
    location = getattr(args, "location", "Osaka")
    days = getattr(args, "days", ["Day 1", "Day 2"])
    cutoff_time_hours = getattr(args, "cutoff_time", 18)
    cutoff_time_minutes = cutoff_time_hours * 60

    logger.info(f"Starting {command} with parameters:")
    logger.info(f"  Hub page: {hub_page}")
    logger.info(f"  Database: {database_name}")
    logger.info(f"  Location: {location}")
    logger.info(f"  Days: {days}")
    logger.info(f"  Cutoff time: {cutoff_time_hours}:00 ({cutoff_time_minutes} minutes)")

    # Create filter and execute
    filter_tool = TravelItineraryFilter(
        hub_page_name=hub_page,
        database_name=database_name,
        location=location,
        days=days,
        cutoff_time_minutes=cutoff_time_minutes
    )

    result = filter_tool.remove_itinerary()

    # Output results
    print("\n" + "=" * 60)
    print("REMOVAL RESULTS")
    print("=" * 60)
    print(f"Success: {result['success']}")
    print(f"Items removed: {result['removed_count']}")
    
    if result["removed_items"]:
        print("\nRemoved items:")
        for item in result["removed_items"]:
            print(f"  ✓ {item['title']} at {item['time']} ({item['day']})")
    
    if result["errors"]:
        print("\nErrors encountered:")
        for error in result["errors"]:
            print(f"  ✗ {error}")
    
    print("=" * 60)

    # Exit with appropriate code
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
