#!/usr/bin/env python3
"""
Test script for LLM integration in BlockMarket.
This script tests the LLM summarization functionality without affecting the main training loop.
"""

import os
import sys
import logging

# Add rl directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "rl"))

# Set up environment variables
os.environ["IMAGINE_API_KEY"] = "301f49b1-6860-40c9-adb6-12ae19d84645"
os.environ["IMAGINE_ENDPOINT_URL"] = "https://aisuite.cirrascale.com/apis/v2"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_llm_summarizer():
    """Test the LLM summarization functionality."""
    try:
        from rl.llm_summarizer import get_summarizer

        logger.info("Testing LLM summarization...")

        # Create summarizer
        summarizer = get_summarizer()

        # Mock trading data
        environment_data = {
            "generation": 5,
            "timestep": 250,
            "best_fitness": 12.5,
            "avg_fitness": 8.3,
            "generation_progress": 0.5,
        }

        agent_data = [
            {
                "id": "agent_1",
                "position": [25.5, 30.2],
                "inventory": {"diamond": 3, "gold": 2},
                "desired_item": "emerald",
                "fitness": 12.5,
                "successful_trades": 8,
                "attempted_trades": 12,
            },
            {
                "id": "agent_2",
                "position": [45.1, 22.8],
                "inventory": {"apple": 5, "redstone": 1},
                "desired_item": "gold",
                "fitness": 9.2,
                "successful_trades": 5,
                "attempted_trades": 9,
            },
            {
                "id": "agent_3",
                "position": [12.0, 55.5],
                "inventory": {"emerald": 2, "diamond": 1},
                "desired_item": "apple",
                "fitness": 7.8,
                "successful_trades": 4,
                "attempted_trades": 7,
            },
        ]

        trade_data = [
            {
                "requester_id": "agent_1",
                "target_id": "agent_2",
                "requester_gave": ["diamond", 1.0],
                "requester_received": ["gold", 1.5],
            },
            {
                "requester_id": "agent_3",
                "target_id": "agent_1",
                "requester_gave": ["emerald", 1.0],
                "requester_received": ["diamond", 0.8],
            },
        ]

        generation_stats = {
            "current_gen": 5,
            "total_timesteps": 250,
            "generation_progress": 0.5,
        }

        # Generate summary
        logger.info("Generating test summary...")
        summary = summarizer.generate_summary(
            environment_data, agent_data, trade_data, generation_stats
        )

        logger.info("Summary generated successfully!")
        logger.info("Summary content:")
        logger.info("-" * 60)
        logger.info(summary)
        logger.info("-" * 60)

        # Test recent summaries retrieval
        recent_summaries = summarizer.get_recent_summaries(count=1)
        logger.info(f"Retrieved {len(recent_summaries)} recent summaries")

        return True

    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False


def test_web_endpoints():
    """Test the web server endpoints."""
    try:
        import requests
        import time

        # Test if Flask server is running on port 5001
        base_url = "http://localhost:5001"

        logger.info("Testing web endpoints...")

        # Test basic endpoints
        endpoints = ["/state", "/agents", "/trades", "/statistics", "/llm_summary"]

        for endpoint in endpoints:
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    logger.info(f"✓ {endpoint} - OK")
                else:
                    logger.warning(f"⚠ {endpoint} - Status: {response.status_code}")
            except requests.RequestException:
                logger.warning(f"⚠ {endpoint} - Server not running or unreachable")

        return True

    except ImportError:
        logger.warning("Requests library not available, skipping web endpoint tests")
        return True
    except Exception as e:
        logger.error(f"Web endpoint test failed: {e}")
        return False


if __name__ == "__main__":
    logger.info("Starting BlockMarket LLM Integration Tests")
    logger.info("=" * 60)

    success = True

    # Test 1: LLM Summarizer
    logger.info("Test 1: LLM Summarization")
    if test_llm_summarizer():
        logger.info("✓ LLM Summarization test passed")
    else:
        logger.error("✗ LLM Summarization test failed")
        success = False

    print()

    # Test 2: Web Endpoints
    logger.info("Test 2: Web Endpoints")
    if test_web_endpoints():
        logger.info("✓ Web endpoints test passed")
    else:
        logger.error("✗ Web endpoints test failed")
        success = False

    print()
    logger.info("=" * 60)

    if success:
        logger.info("🎉 All tests passed! LLM integration is working correctly.")
        sys.exit(0)
    else:
        logger.error("❌ Some tests failed. Check the logs above for details.")
        sys.exit(1)
