"""
Test script for Web Search Workflow.

Usage:
    python test_websearch.py

This script tests the web search capabilities of Gemini 2.0/2.5 models.
"""
import os
import sys
import asyncio
from dotenv import load_dotenv

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

load_dotenv()

from app.workflows.websearch_workflow import WebSearchWorkflow


async def test_web_search():
    """Test the web search workflow."""
    
    # Get API token from environment
    api_token = os.getenv("API_Token")
    if not api_token:
        print("Error: API_Token not found in .env file")
        return
    
    print("=" * 80)
    print("Web Search Workflow Test")
    print("=" * 80)
    print()
    
    # Create workflow
    workflow = WebSearchWorkflow(
        api_key=api_token,
        thread_id="test-websearch-123"
    )
    
    # Initialize
    print("Initializing workflow...")
    await workflow.initialize()
    print("Workflow initialized\n")
    
    # Test queries
    test_queries = [
        "What is the exact date today and the latest news in Germany? Give me the used URLs.",
        "What are the top technology trends in 2026?",
        "What is the weather in Tokyo right now in Celsius?",
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'=' * 80}")
        print(f"Test Query #{i}:")
        print(f"{'=' * 80}")
        print(f"Q: {query}\n")
        
        result = await workflow.search(query, verbose=True)
        
        if result["status"] == "success":
            print(f"\n Success!")
            print(f"Model: {result['model']}")
            print(f"Agent: {result['agent']}")
            print(f"\nResponse:")
            print("-" * 80)
            print(result["result"])
            print("-" * 80)
        else:
            print(f"\nError: {result.get('error')}")
        
        print()
    
    # Cleanup
    await workflow.cleanup()
    print("\nAll tests completed!")


async def interactive_mode():
    """Run interactive web search mode."""
    
    api_token = os.getenv("API_Token")
    if not api_token:
        print("Error: API_Token not found in .env file")
        return
    
    print("=" * 80)
    print("Interactive Web Search Mode")
    print("=" * 80)
    print("Type 'exit' or 'quit' to stop\n")
    
    workflow = WebSearchWorkflow(
        api_key=api_token,
        thread_id="interactive-websearch"
    )
    
    await workflow.initialize()
    print("Ready for searches!\n")
    
    while True:
        try:
            query = input("\nEnter your search query: ").strip()
            
            if query.lower() in ['exit', 'quit', 'q']:
                break
            
            if not query:
                continue
            
            print()
            result = await workflow.search(query, verbose=False)
            
            if result["status"] == "success":
                print(f"\nResponse:\n{result['result']}")
            else:
                print(f"\nError: {result.get('error')}")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\nError: {e}")
    
    await workflow.cleanup()
    print("\nGoodbye!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Web Search Workflow")
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive mode"
    )
    
    args = parser.parse_args()
    
    if args.interactive:
        asyncio.run(interactive_mode())
    else:
        asyncio.run(test_web_search())
