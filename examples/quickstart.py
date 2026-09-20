"""
Quickstart example for Cortex Core.
"""

import logging

from cortex_core import create_cortex

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Quickstart example."""
    print("=" * 60)
    print("Cortex Core Quickstart")
    print("=" * 60)

    try:
        # Create Cortex Core instance
        print("\n1. Creating Cortex Core instance...")
        cortex = create_cortex(mode="adaptive", security_key="demo-security-key-123")

        # Check system status
        print("\n2. Checking system status...")
        status = cortex.get_status()
        print(f"   Status: {status['status']}")
        print(f"   Mode: {status['mode']}")
        print(f"   Components: {len(status['components'])} healthy")

        # Process sample intelligence data
        print("\n3. Processing intelligence data...")

        intelligence_data = {
            "type": "threat_intelligence",
            "source": "network_sensors",
            "data": {
                "ip_address": "192.168.1.100",
                "port": 443,
                "protocol": "HTTPS",
                "anomaly_score": 0.85,
                "timestamp": "2024-01-15T10:30:00Z",
            },
            "priority": "high",
        }

        result = cortex.process(intelligence_data)

        print("\n4. Processing Results:")
        print(f"   Success: {result['success']}")
        if result["success"]:
            print(f"   Decision: {result.get('decision', 'N/A')}")
            print(f"   Processing time: {result.get('processing_time', 0):.3f}s")
            print(f"   Memory ID: {result.get('memory_id', 'N/A')}")
        else:
            print(f"   Error: {result.get('error', 'Unknown error')}")

        # Show metrics
        print("\n5. Performance Metrics:")
        metrics = cortex.get_status()["metrics"]
        print(f"   Total processed: {metrics['total_processed']}")
        print(f"   Success rate: {metrics['success_rate']:.1%}")
        print(f"   Avg processing time: {metrics['avg_processing_time']:.3f}s")

        # Shutdown
        print("\n6. Shutting down...")
        cortex.shutdown()

        print("\n✅ Quickstart completed successfully!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise


if __name__ == "__main__":
    main()
