#!/usr/bin/env python3
"""
Client for testing and automating the Travel Booking Agent REST API.
This script makes requests to the FastAPI agent and displays responses.
"""

import requests
import json
import time
import logging
import os
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger("client")


class TravelAgentClient:
    """Client for interacting with Travel Booking Agent API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
    
    def health_check(self) -> bool:
        """Check if the agent is healthy"""
        try:
            url = f"{self.base_url}/health"
            response = self.session.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            logger.info(f"✓ Agent is healthy - Model: {data.get('model')}")
            return True
        except Exception as e:
            logger.error(f"✗ Health check failed: {e}")
            return False
    
    def query(self, question: str) -> Optional[str]:
        """Send a query to the agent and get response"""
        try:
            url = f"{self.base_url}/query"
            
            logger.info(f"📤 Sending query: {question[:80]}...")
            start_time = time.time()
            
            response = self.session.post(
                url,
                json={"query": question},
                timeout=300  # 5 minute timeout for agentic tasks
            )
            
            elapsed = time.time() - start_time
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("success"):
                logger.info(f"✓ Received response in {elapsed:.2f}s")
                return data.get("response")
            else:
                error = data.get("error", "Unknown error")
                logger.error(f"✗ Agent error: {error}")
                return None
        
        except requests.exceptions.Timeout:
            logger.error("✗ Request timed out - agent may be processing or unresponsive")
            return None
        except requests.exceptions.ConnectionError:
            logger.error(f"✗ Connection failed - is the agent running at {self.base_url}?")
            return None
        except Exception as e:
            logger.error(f"✗ Query failed: {e}")
            return None
    
    def reset_conversation(self) -> bool:
        """Reset the conversation history"""
        try:
            url = f"{self.base_url}/reset"
            response = self.session.post(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            if data.get("success"):
                logger.info("✓ Conversation reset successfully")
                return True
            else:
                logger.error("✗ Failed to reset conversation")
                return False
        except Exception as e:
            logger.error(f"✗ Reset failed: {e}")
            return False
    
    def get_conversation_info(self) -> Optional[dict]:
        """Get current conversation information"""
        try:
            url = f"{self.base_url}/conversation-info"
            response = self.session.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            logger.info(f"✓ Conversation info: {data['user_turns']} user turns, {data['assistant_turns']} assistant turns")
            return data
        except Exception as e:
            logger.error(f"✗ Failed to get conversation info: {e}")
            return None
    
    def print_response(self, response: str):
        """Pretty print agent response"""
        print("\n" + "="*70)
        print("🤖 AGENT RESPONSE:")
        print("="*70)
        print(response)
        print("="*70 + "\n")


def run_sample_scenarios(client: TravelAgentClient):
    """Run sample booking scenarios"""
    
    scenarios = [
        {
            "name": "Standard Booking Request",
            "query": (
                "I want to book a travel tour. My phone number is +919999999999. "
                "I'm interested in Goa with a budget of 40000."
            ),
        },
        {
            "name": "Complex Booking with Details",
            "query": (
                "Hi! I'm looking for a travel package to Goa. Phone: +919999999999. "
                "Budget around 40000. I prefer 3-4 star hotels and non-veg meals. "
                "Can you help me find something starting from next month?"
            ),
        },
        {
            "name": "Customer Service Inquiry",
            "query": (
                "I have phone number +919999999999. Can you look up my customer profile? "
                "I might be interested in booking something soon."
            ),
        },
        {
            "name": "Booking With Payment Consent",
            "query": (
                "I want to book the Goa tour. My phone is +919999999999. "
                "Budget 40000. I consent to pay by card (last4 4242) and authorize the charge."
            ),
        },
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{'#'*70}")
        print(f"# Scenario {i}: {scenario['name']}")
        print(f"{'#'*70}")
        print(f"📝 Query: {scenario['query']}")
        
        response = client.query(scenario['query'])
        
        if response:
            client.print_response(response)
        else:
            print("❌ Failed to get response from agent\n")
        
        if i < len(scenarios):
            logger.info("Waiting before next scenario...")
            time.sleep(2)


def interactive_mode(client: TravelAgentClient):
    """Run in interactive mode for manual testing"""
    print("\n" + "="*70)
    print("🎯 Travel Booking Agent - Interactive Mode")
    print("="*70)
    print("Commands:")
    print("  - Type your query and press Enter to send")
    print("  - Type 'reset' to start a new conversation")
    print("  - Type 'info' to see conversation status")
    print("  - Type 'health' to check agent status")
    print("  - Type 'quit' or 'exit' to close")
    print("\n💡 Tip: The agent remembers the entire conversation context!")
    print("    Provide details once and refer back to them naturally.")
    print("="*70 + "\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["quit", "exit"]:
                print("👋 Goodbye!")
                break
            
            if user_input.lower() == "health":
                client.health_check()
                continue
            
            if user_input.lower() == "reset":
                if client.reset_conversation():
                    print("✓ Conversation reset. Start fresh!\n")
                else:
                    print("✗ Failed to reset conversation\n")
                continue
            
            if user_input.lower() == "info":
                info = client.get_conversation_info()
                if info:
                    print(f"\nℹ️  Conversation Status:")
                    print(f"   Total messages: {info['total_messages']}")
                    print(f"   Your turns: {info['user_turns']}")
                    print(f"   Agent turns: {info['assistant_turns']}")
                    print(f"   Active: {'Yes' if info['conversation_active'] else 'No'}\n")
                else:
                    print("✗ Failed to get conversation info\n")
                continue
            
            response = client.query(user_input)
            if response:
                client.print_response(response)
        
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            logger.error(f"Error: {e}")


def main():
    """Main entry point"""
    # Get agent URL from environment or use default
    agent_url = os.getenv("AGENT_URL", "http://localhost:8000")
    
    client = TravelAgentClient(base_url=agent_url)
    
    logger.info(f"Travel Booking Agent Client")
    logger.info(f"Agent URL: {agent_url}")
    
    # Check if agent is running
    logger.info("Checking agent connectivity...")
    if not client.health_check():
        print("\n⚠️  Agent is not responding. Make sure it's running:")
        print(f"   python agent/agent.py")
        print(f"   or: AGENT_URL={agent_url} python agent/client.py")
        return
    
    # Check for command line arguments
    import sys
    if len(sys.argv) > 1:
        # Run in automation mode with sample scenarios
        if sys.argv[1] == "--samples":
            logger.info("Running sample scenarios...")
            run_sample_scenarios(client)
        else:
            # Treat remaining args as a query
            query = " ".join(sys.argv[1:])
            response = client.query(query)
            if response:
                client.print_response(response)
    else:
        # Interactive mode
        interactive_mode(client)


if __name__ == "__main__":
    main()
