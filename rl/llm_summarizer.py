"""
LLM-powered summarization module for BlockMarket trading analysis.
Uses the Imagine SDK to provide real-time insights on trading patterns and agent behavior.
"""

import os
import logging
import time
from typing import List, Dict, Any, Optional
from threading import Lock
from collections import deque

# LangChain integration with Imagine SDK
try:
    from langchain_core.messages import HumanMessage, SystemMessage
    import requests
except ImportError:
    print(
        "LangChain dependencies not installed. Run: pip install langchain langchain-core requests"
    )
    raise

logger = logging.getLogger(__name__)


class ImagineChat:
    """Custom implementation of Imagine SDK chat interface."""

    def __init__(self, model="Llama-3.1-8B", max_tokens=200):
        self.model = model
        self.max_tokens = max_tokens
        self.api_key = os.getenv(
            "IMAGINE_API_KEY", "301f49b1-6860-40c9-adb6-12ae19d84645"
        )
        self.endpoint = os.getenv(
            "IMAGINE_ENDPOINT_URL", "https://aisuite.cirrascale.com/apis/v2"
        )

        if not self.api_key or not self.endpoint:
            raise ValueError("IMAGINE_API_KEY and IMAGINE_ENDPOINT_URL must be set")

    def invoke(self, messages):
        """Send messages to Imagine API and get response."""
        try:
            # Convert LangChain messages to API format
            api_messages = []
            for msg in messages:
                if hasattr(msg, "content"):
                    if isinstance(msg, SystemMessage):
                        api_messages.append({"role": "system", "content": msg.content})
                    elif isinstance(msg, HumanMessage):
                        api_messages.append({"role": "user", "content": msg.content})

            # API request payload
            payload = {
                "model": self.model,
                "messages": api_messages,
                "max_tokens": self.max_tokens,
                "temperature": 0.7,
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            # Make API request
            response = requests.post(
                f"{self.endpoint}/chat/completions",
                json=payload,
                headers=headers,
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                return type("Response", (), {"content": content})()
            else:
                logger.error(
                    f"Imagine API error: {response.status_code} - {response.text}"
                )
                return type(
                    "Response", (), {"content": "Summary unavailable due to API error."}
                )()

        except Exception as e:
            logger.error(f"Error calling Imagine API: {e}")
            return type(
                "Response",
                (),
                {"content": "Summary unavailable due to connection error."},
            )()


class TradingSummarizer:
    """
    Generates AI-powered summaries of trading environment activity using Imagine SDK.
    """

    def __init__(self):
        """Initialize the summarizer with Imagine LLM."""
        self.model = ImagineChat(model="Llama-3.1-8B", max_tokens=300)
        self.summaries = deque(maxlen=20)  # Keep last 20 summaries
        self.lock = Lock()

        # System prompt for trading analysis
        self.system_prompt = """You are an expert financial analyst specializing in algorithmic trading and multi-agent systems. 
        
        You analyze trading data from a reinforcement learning environment where AI agents learn to trade items (diamond, gold, apple, emerald, redstone) to maximize their fitness.

        Key concepts:
        - Agents have inventories and desire specific items
        - They use neural networks to learn optimal trading strategies
        - Fitness is based on acquiring desired items
        - Genetic algorithms evolve the population each generation
        - Spatial positioning affects trade probability

        Provide concise, insightful analysis focusing on:
        1. Trading patterns and market dynamics
        2. Agent performance and learning progress
        3. Key trends and anomalies
        4. Strategic insights for improvement

        Keep responses under 250 words and use financial/trading terminology."""

    def generate_summary(
        self,
        environment_data: Dict[str, Any],
        agent_data: List[Dict],
        trade_data: List[Dict],
        generation_stats: Dict[str, Any],
    ) -> str:
        """
        Generate an AI-powered summary of current trading environment state.

        Args:
            environment_data: Current environment statistics
            agent_data: List of agent information
            trade_data: Recent trade history
            generation_stats: Generation performance metrics

        Returns:
            AI-generated summary string
        """
        try:
            # Prepare data for LLM analysis
            summary_data = self._prepare_analysis_data(
                environment_data, agent_data, trade_data, generation_stats
            )

            # Create prompt
            user_prompt = f"""Analyze this BlockMarket trading data:

ENVIRONMENT STATUS:
- Generation: {environment_data.get("generation", 0)}
- Timestep: {environment_data.get("timestep", 0)}
- Active Agents: {len(agent_data)}
- Recent Trades: {len(trade_data)}

PERFORMANCE METRICS:
- Best Fitness: {environment_data.get("best_fitness", 0):.2f}
- Average Fitness: {environment_data.get("avg_fitness", 0):.2f}
- Generation Progress: {environment_data.get("generation_progress", 0) * 100:.1f}%

MARKET ACTIVITY:
{summary_data["market_analysis"]}

AGENT INSIGHTS:
{summary_data["agent_analysis"]}

TRADING PATTERNS:
{summary_data["trade_analysis"]}

Provide a concise market analysis highlighting key trends, performance insights, and strategic observations."""

            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=user_prompt),
            ]

            # Get LLM response
            start_time = time.time()
            response = self.model.invoke(messages)
            response_time = time.time() - start_time

            summary = response.content

            # Store summary with metadata
            summary_entry = {
                "timestamp": time.time(),
                "generation": environment_data.get("generation", 0),
                "timestep": environment_data.get("timestep", 0),
                "summary": summary,
                "response_time": response_time,
                "data_points": {
                    "agents": len(agent_data),
                    "trades": len(trade_data),
                    "best_fitness": environment_data.get("best_fitness", 0),
                    "avg_fitness": environment_data.get("avg_fitness", 0),
                },
            }

            with self.lock:
                self.summaries.append(summary_entry)

            logger.info(
                "Generated LLM summary in %.2fs for generation %s",
                response_time,
                environment_data.get("generation", 0),
            )
            return summary

        except requests.RequestException as e:
            logger.error("Error generating summary: %s", e)
            return f"Summary generation failed: {str(e)}"

    def _prepare_analysis_data(
        self,
        environment_data: Dict,
        agent_data: List[Dict],
        trade_data: List[Dict],
        generation_stats: Dict,
    ) -> Dict[str, str]:  # pylint: disable=unused-argument
        """Prepare structured data for LLM analysis."""

        # Market analysis
        if agent_data:
            fitness_values = [agent.get("fitness", 0) for agent in agent_data]
            top_agents = sorted(
                agent_data, key=lambda x: x.get("fitness", 0), reverse=True
            )[:3]

            market_analysis = f"""
- Fitness Range: {min(fitness_values):.2f} to {max(fitness_values):.2f}
- Top 3 Agents: {", ".join([f"{agent.get('id', 'Unknown')} ({agent.get('fitness', 0):.2f})" for agent in top_agents])}
- Performance Spread: {max(fitness_values) - min(fitness_values):.2f}
"""
        else:
            market_analysis = "No agent data available"

        # Agent analysis
        if agent_data:
            desired_items = {}
            successful_trades = sum(
                agent.get("successful_trades", 0) for agent in agent_data
            )
            attempted_trades = sum(
                agent.get("attempted_trades", 0) for agent in agent_data
            )

            for agent in agent_data:
                item = agent.get("desired_item", "unknown")
                desired_items[item] = desired_items.get(item, 0) + 1

            success_rate = (
                (successful_trades / attempted_trades * 100)
                if attempted_trades > 0
                else 0
            )

            agent_analysis = f"""
- Trade Success Rate: {success_rate:.1f}% ({successful_trades}/{attempted_trades})
- Item Demand Distribution: {dict(desired_items)}
- Agent Specialization: {len(desired_items)} different item types targeted
"""
        else:
            agent_analysis = "No agent activity data"

        # Trade analysis
        if trade_data:
            recent_trades = trade_data[-10:]  # Last 10 trades
            trade_pairs = {}

            for trade in recent_trades:
                requester_gave = trade.get("requester_gave", ["unknown", 0])
                requester_received = trade.get("requester_received", ["unknown", 0])
                pair = f"{requester_gave[0]}→{requester_received[0]}"
                trade_pairs[pair] = trade_pairs.get(pair, 0) + 1

            popular_trades = sorted(
                trade_pairs.items(), key=lambda x: x[1], reverse=True
            )[:3]

            trade_analysis = f"""
- Recent Activity: {len(recent_trades)} trades in last period
- Popular Exchanges: {", ".join([f"{pair} ({count}x)" for pair, count in popular_trades])}
- Market Liquidity: {"High" if len(recent_trades) > 5 else "Moderate" if len(recent_trades) > 2 else "Low"}
"""
        else:
            trade_analysis = "No recent trading activity"

        return {
            "market_analysis": market_analysis.strip(),
            "agent_analysis": agent_analysis.strip(),
            "trade_analysis": trade_analysis.strip(),
        }

    def get_recent_summaries(self, count: int = 5) -> List[Dict]:
        """Get the most recent summaries."""
        with self.lock:
            return list(self.summaries)[-count:]

    def get_latest_summary(self) -> Optional[Dict]:
        """Get the most recent summary."""
        with self.lock:
            return self.summaries[-1] if self.summaries else None

    def clear_summaries(self):
        """Clear all stored summaries."""
        with self.lock:
            self.summaries.clear()


# Global summarizer instance
_summarizer = None


def get_summarizer() -> TradingSummarizer:
    """Get or create the global summarizer instance."""
    global _summarizer  # pylint: disable=global-statement
    if _summarizer is None:
        _summarizer = TradingSummarizer()
    return _summarizer
