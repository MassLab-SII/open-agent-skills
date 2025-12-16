import os
from notion_client import Client
import sys
from dotenv import load_dotenv


# Compatibility layer for notion-client >= 2.7.0 which uses data_sources.query instead of databases.query
class DatabasesQueryCompat:
    """Compatibility wrapper to support databases.query() in newer notion-client versions."""
    
    def __init__(self, parent_client):
        self.parent_client = parent_client
        self._original = parent_client.databases
        self._cache = {}  # Cache for database ID mappings
    
    def __getattr__(self, name):
        return getattr(self._original, name)
    
    def query(self, database_id, **kwargs):
        """Query a database using data_sources.query() for compatibility."""
        first_error = None
        
        # First, try using the ID directly
        try:
            return self.parent_client.data_sources.query(
                data_source_id=database_id,
                **kwargs
            )
        except Exception as e:
            first_error = e
        
        # If that fails, it might be a child_database block ID
        # Try to retrieve the block and get its title
        try:
            block = self.parent_client.blocks.retrieve(block_id=database_id)
            if block.get("type") == "child_database":
                db_title = block.get("child_database", {}).get("title", "")
                if db_title:
                    # Search for a data_source with this title
                    response = self.parent_client.search(query=db_title)
                    for result in response.get("results", []):
                        if result.get("object") == "data_source":
                            result_id = result.get("id")
                            try:
                                return self.parent_client.data_sources.query(
                                    data_source_id=result_id,
                                    **kwargs
                                )
                            except Exception:
                                continue
        except Exception:
            pass
        
        # If that fails, try to search for all data_sources
        try:
            response = self.parent_client.search(query="")
            for result in response.get("results", []):
                if result.get("object") == "data_source":
                    result_id = result.get("id")
                    try:
                        return self.parent_client.data_sources.query(
                            data_source_id=result_id,
                            **kwargs
                        )
                    except Exception:
                        continue
        except Exception:
            pass
        
        # Fallback to original databases.query if it exists
        try:
            if hasattr(self._original, 'query'):
                return self._original.query(database_id=database_id, **kwargs)
        except Exception:
            pass
        
        # If all else fails, raise the original error
        if first_error:
            raise first_error
        raise Exception(f"Could not query database {database_id}")


def get_notion_client():
    # Construct the absolute path to the .env file in the project root
    load_dotenv(dotenv_path=".mcp_env")
    api_key = os.getenv("EVAL_NOTION_API_KEY")
    if not api_key:
        print(
            "Error: EVAL_NOTION_API_KEY not found in environment variables.",
            file=sys.stderr,
        )
        sys.exit(1)
    client = Client(auth=api_key)
    
    # Add compatibility layer for databases.query()
    client.databases = DatabasesQueryCompat(client)
    
    return client


def _find_object(notion: Client, title: str, object_type: str):
    """Generic helper to find a Notion page or database by title.

    Args:
        notion: Authenticated Notion Client.
        title: Title (or partial title) to search for.
        object_type: Either "page", "database", or "data_source".

    Returns:
        The ID string if found, otherwise None.
    """
    # Map object_type to API values
    api_type = object_type
    if object_type == "database":
        # In newer Notion API, databases are returned as "data_source"
        api_type = "data_source"
    
    try:
        search_results = (
            notion.search(
                query=title, filter={"property": "object", "value": api_type}
            ).get("results")
            or []
        )
    except Exception:
        # If the filter fails, try without filter
        search_results = notion.search(query=title).get("results", [])

    if not search_results:
        return None

    # Shortcut when there is only one match
    if len(search_results) == 1:
        return search_results[0]["id"]

    # Attempt to find a case-insensitive match on the title field
    for result in search_results:
        if object_type == "page":
            # Pages store their title inside the "properties.title.title" rich text list
            title_rich_texts = (
                result.get("properties", {}).get("title", {}).get("title", [])
            )
        else:  # database or data_source
            title_rich_texts = result.get("title", [])

        for text_obj in title_rich_texts:
            if title.lower() in text_obj.get("plain_text", "").lower():
                return result["id"]

    # Fallback: return the first result
    return search_results[0]["id"]


def find_page(notion: Client, page_title: str):
    """Finds a page by title. Wrapper around _find_object with object_type='page'."""
    return _find_object(notion, page_title, "page")


def get_page_by_id(notion: Client, page_id: str):
    """Gets a page by its ID. Returns the page object if found, None otherwise."""
    try:
        return notion.pages.retrieve(page_id=page_id)
    except Exception:
        return None


def find_page_by_id(notion: Client, page_id: str):
    """Finds a page by its ID and returns the ID if it exists, None otherwise."""
    try:
        notion.pages.retrieve(page_id=page_id)
        return page_id
    except Exception:
        return None


def find_database_by_id(notion: Client, database_id: str):
    """Finds a database by its ID and returns the ID if it exists, None otherwise."""
    try:
        notion.databases.retrieve(database_id=database_id)
        return database_id
    except Exception:
        return None


def find_page_or_database_by_id(notion: Client, object_id: str):
    """
    Finds either a page or database by ID. Returns a tuple (object_id, object_type)
    where object_type is either 'page' or 'database', or (None, None) if not found.
    """
    # Try as page first
    try:
        notion.pages.retrieve(page_id=object_id)
        return (object_id, "page")
    except Exception:
        pass

    # Try as database
    try:
        notion.databases.retrieve(database_id=object_id)
        return (object_id, "database")
    except Exception:
        pass

    return (None, None)


def find_database(notion: Client, db_title: str):
    """Finds a database by title. Wrapper around _find_object with object_type='database'."""
    return _find_object(notion, db_title, "database")


def find_database_in_block(notion: Client, block_id: str, db_title: str):
    """
    Recursively find a database by title within a block.
    First looks for child_database blocks, then searches for the actual queryable database ID.
    Returns the data_source ID that can be used with data_sources.query().
    """
    blocks = notion.blocks.children.list(block_id=block_id).get("results")
    for block in blocks:
        if (
            block.get("type") == "child_database"
            and block.get("child_database", {}).get("title") == db_title
        ):
            # Found the child_database block
            # Now we need to find the actual queryable database ID
            # Search for a data_source with the same name
            try:
                search_results = notion.search(query=db_title).get("results", [])
                for result in search_results:
                    if result.get("object") == "data_source":
                        # Found a data_source, check if its title matches
                        result_title = result.get("title", [])
                        if result_title and isinstance(result_title, list):
                            result_title_text = "".join([t.get("plain_text", "") for t in result_title])
                        else:
                            result_title_text = str(result_title)
                        
                        if db_title.lower() in result_title_text.lower():
                            # This is the queryable database ID
                            return result["id"]
            except Exception:
                pass
            
            # Fallback: return the child_database block ID
            # (the compatibility layer should handle it)
            return block["id"]
        
        if block.get("has_children"):
            db_id = find_database_in_block(notion, block["id"], db_title)
            if db_id:
                return db_id
    return None


def get_all_blocks_recursively(notion: Client, block_id: str):
    """
    Recursively fetches all blocks from a starting block ID and its children,
    returning a single flat list of block objects.
    """
    all_blocks = []
    try:
        direct_children = notion.blocks.children.list(block_id=block_id).get(
            "results", []
        )
    except Exception:
        return []

    for block in direct_children:
        all_blocks.append(block)
        if block.get("has_children"):
            all_blocks.extend(get_all_blocks_recursively(notion, block["id"]))

    return all_blocks


def get_block_plain_text(block):
    """
    Safely extract plain_text from a block (paragraph, heading, etc.).
    """
    block_type = block.get("type")
    if not block_type:
        return ""

    block_content = block.get(block_type)
    if not block_content:
        return ""

    rich_text_list = block_content.get("rich_text", [])
    plain_text = "".join([rt.get("plain_text", "") for rt in rich_text_list])

    return plain_text
