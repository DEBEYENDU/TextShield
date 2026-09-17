"""CLI for research."""

from .request_manager import ResearchRequestManager
from .repository import ResearchRepository

def main():
    mgr = ResearchRequestManager(ResearchRepository())
    print("Research CLI ready")
    # Example
    rid = mgr.create_request("IOC_ENRICHMENT", "example.com", "domain")
    print(f"Created research {rid}")

if __name__ == "__main__":
    main()
