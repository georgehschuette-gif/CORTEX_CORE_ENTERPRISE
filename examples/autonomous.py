"""
Advanced Cortex Core Example - Autonomous Intelligence Processing
"""

import asyncio
import logging
import json
from typing import Dict, Any, List
from cortex_core import create_cortex, create_distributed_cortex

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AutonomousAgent:
    """
    Example autonomous agent using Cortex Core.
    """

    def __init__(self):
        self.cortex = create_cortex(
            mode="adaptive",
            security_key="demo-security-key-123"
        )
        self.memory = []
        self.goals = [
            "Analyze security threats",
            "Optimize system performance",
            "Generate insights from data",
            "Learn from interactions"
        ]

    async def run_autonomous_cycle(self):
        """
        Run an autonomous intelligence cycle.
        """
        logger.info("🤖 Starting autonomous intelligence cycle")

        # Phase 1: Gather intelligence
        intelligence_data = await self.gather_intelligence()

        # Phase 2: Process through cognitive pipeline
        insights = []
        for data in intelligence_data:
            result = self.cortex.process(data)
            if result['success']:
                insights.append(result)
                logger.info(f"✓ Processed intelligence: {result['decision']}")
            else:
                logger.warning(f"✗ Failed to process: {result['error']}")

        # Phase 3: Learn and adapt
        await self.learn_from_insights(insights)

        # Phase 4: Generate actions
        actions = await self.generate_actions(insights)

        # Phase 5: Execute actions
        await self.execute_actions(actions)

        logger.info("🔄 Autonomous cycle completed")

    async def gather_intelligence(self) -> List[Dict[str, Any]]:
        """
        Gather intelligence from various sources.
        """
        logger.info("🔍 Gathering intelligence...")

        # Simulate different types of intelligence data
        intelligence_sources = [
            {
                "type": "network_traffic",
                "source": "firewall_logs",
                "data": {
                    "connections": 15420,
                    "blocked_attempts": 23,
                    "unusual_patterns": 5,
                    "timestamp": "2024-01-15T10:30:00Z"
                },
                "priority": "high"
            },
            {
                "type": "system_metrics",
                "source": "monitoring_system",
                "data": {
                    "cpu_usage": 67.5,
                    "memory_usage": 82.3,
                    "disk_io": 1240,
                    "network_io": 890,
                    "active_processes": 156,
                    "timestamp": "2024-01-15T10:30:00Z"
                },
                "priority": "medium"
            },
            {
                "type": "user_behavior",
                "source": "application_logs",
                "data": {
                    "active_users": 1247,
                    "session_duration_avg": 1845,  # seconds
                    "error_rate": 0.023,
                    "feature_usage": {
                        "search": 0.45,
                        "analytics": 0.32,
                        "reports": 0.23
                    },
                    "timestamp": "2024-01-15T10:30:00Z"
                },
                "priority": "medium"
            }
        ]

        return intelligence_sources

    async def learn_from_insights(self, insights: List[Dict[str, Any]]):
        """
        Learn from processing insights.
        """
        logger.info("🧠 Learning from insights...")

        # Store insights in memory
        for insight in insights:
            self.memory.append({
                'timestamp': insight.get('metadata', {}).get('timestamp'),
                'decision': insight.get('decision'),
                'analysis': insight.get('analysis'),
                'processing_time': insight.get('processing_time')
            })

        # Limit memory size
        if len(self.memory) > 100:
            self.memory = self.memory[-100:]

        # Analyze patterns in decisions
        decision_counts = {}
        for item in self.memory[-20:]:  # Last 20 decisions
            decision = item['decision']
            decision_counts[decision] = decision_counts.get(decision, 0) + 1

        logger.info(f"Decision patterns: {decision_counts}")

    async def generate_actions(self, insights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate actions based on insights.
        """
        logger.info("🎯 Generating actions...")

        actions = []

        for insight in insights:
            decision = insight.get('decision', '')

            if 'PROCEED' in decision:
                actions.append({
                    'type': 'optimize',
                    'target': 'system_performance',
                    'reason': 'Positive analysis results',
                    'confidence': insight.get('processing_time', 0)
                })
            elif 'REVIEW' in decision:
                actions.append({
                    'type': 'investigate',
                    'target': 'anomalies',
                    'reason': 'Potential issues detected',
                    'priority': 'high'
                })

        return actions

    async def execute_actions(self, actions: List[Dict[str, Any]]):
        """
        Execute generated actions.
        """
        logger.info("⚡ Executing actions...")

        for action in actions:
            action_type = action['type']

            if action_type == 'optimize':
                logger.info(f"🔧 Optimizing {action['target']}")
                # Simulate optimization
                await asyncio.sleep(0.1)

            elif action_type == 'investigate':
                logger.info(f"🔍 Investigating {action['target']}")
                # Simulate investigation
                await asyncio.sleep(0.2)

            logger.info(f"✓ Action completed: {action['type']}")

    async def monitor_and_adapt(self):
        """
        Continuously monitor and adapt behavior.
        """
        logger.info("📊 Starting continuous monitoring...")

        cycle_count = 0
        while True:
            try:
                cycle_count += 1
                logger.info(f"🔄 Starting cycle #{cycle_count}")

                await self.run_autonomous_cycle()

                # Get system status
                status = self.cortex.get_status()
                logger.info(f"System health: {status['status']}")

                # Adapt based on performance
                await self.adapt_behavior(status)

                # Wait before next cycle
                await asyncio.sleep(30)  # 30 second cycles

            except Exception as e:
                logger.error(f"Error in monitoring cycle: {e}")
                await asyncio.sleep(10)

    async def adapt_behavior(self, status: Dict[str, Any]):
        """
        Adapt behavior based on system status.
        """
        metrics = status.get('metrics', {})

        # Adapt based on success rate
        success_rate = metrics.get('success_rate', 0)
        if success_rate < 0.8:
            logger.warning("Low success rate detected, adjusting processing mode")
            # Could switch to more conservative mode

        # Adapt based on processing time
        avg_time = metrics.get('avg_processing_time', 0)
        if avg_time > 2.0:
            logger.warning("High processing time detected, optimizing performance")
            # Could enable caching or optimization

async def main():
    """Main autonomous agent demonstration."""
    print("=" * 70)
    print("🤖 Cortex Core Autonomous Agent Demo")
    print("=" * 70)

    try:
        # Create autonomous agent
        agent = AutonomousAgent()

        # Get initial system status
        print("\n1. Initializing system...")
        status = agent.cortex.get_status()
        print(f"   Status: {status['status']}")
        print(f"   Mode: {status['mode']}")
        print(f"   Components: {len(status['components'])} active")

        # Run a few autonomous cycles
        print("\n2. Running autonomous intelligence cycles...")

        for i in range(3):
            print(f"\n   Cycle {i+1}:")
            await agent.run_autonomous_cycle()
            await asyncio.sleep(2)  # Brief pause between cycles

        # Show final status
        print("\n3. Final system status:")
        final_status = agent.cortex.get_status()
        metrics = final_status['metrics']
        print(f"   Total processed: {metrics['total_processed']}")
        print(".1%")
        print(".3f")
        print(".1f")

        print("\n4. Memory contents (last 5 entries):")
        for i, memory_item in enumerate(agent.memory[-5:]):
            print(f"   {i+1}. Decision: {memory_item['decision'][:50]}...")

        print("\n✅ Autonomous agent demonstration completed!")
        print("\n💡 Key capabilities demonstrated:")
        print("   • Multi-source intelligence gathering")
        print("   • Cognitive processing pipeline")
        print("   • Learning and adaptation")
        print("   • Autonomous action generation")
        print("   • Continuous monitoring and improvement")

        # Cleanup
        agent.cortex.shutdown()

    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
