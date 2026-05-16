# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "fastmcp",
# ]
# ///

from fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP("{{NAME}}")

@mcp.tool()
def sample_tool(param: str) -> str:
    """
    A sample tool for the {{NAME}} server.
    Provide a clear description so the agent knows when to use this.
    """
    return f"Processed {param} in {{NAME}}"

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
