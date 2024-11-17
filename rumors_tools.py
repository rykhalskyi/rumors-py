from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import tool

from dotenv import load_dotenv

load_dotenv()

tavily_tool = TavilySearchResults(max_results=5)

@tool
def show_for_user(info):
    """
    Makes user friendly output

    Example call:

    show_for_user("Some info")
    Args:
        info (str): The information which should be shown to user
    Returns:
        returns string
    """
    print(f"Show for the User {info}")
    return "If you have completed all tasks, respond with FINAL ANSWER." 