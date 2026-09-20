"""
Distributed Cortex Core implementation.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from cortex_core.core.cortex_core import CortexCore
from cortex_core.distributed.consensus import RaftConsensus
from cortex_core.distributed.coordinator import DistributedCoordinator
from cortex_core.exceptions import DistributedError

logger = logging.getLogger(__name__)


@dataclass
class NodeInfo:
    """Information about a cluster node."""

    node_id: str
    address: str
    status: str  # leader, follower, candidate
    health: Dict[str, Any]
    last_seen: datetime


class DistributedCortexCore(CortexCore):
    """
    Distributed Cortex Core with cluster capabilities.

    Extends CortexCore with distributed computing features.
    """

    def __init__(
        self,
        node_id: str,
        peers: List[str],
        config: Dict[str, Any],
        bootstrap_node: Optional[str] = None,
        consensus_factory: Optional[Callable[..., "RaftConsensus"]] = None,
    ):
        """
        Initialize distributed Cortex Core.

        Args:
            node_id: Unique node identifier
            peers: List of peer addresses
            config: Configuration
            bootstrap_node: Bootstrap node for joining cluster
            consensus_factory: Optional callable returning a RaftConsensus
                instance. Defaults to the real RaftConsensus class.
                Provided as a seam for dependency injection and testing.
        """
        super().__init__(config, security_key=None)

        self.node_id = node_id
        self.peers = peers
        self.bootstrap_node = bootstrap_node

        # Distributed components
        self.consensus = None
        self.coordinator = None

        # Node registry
        self.nodes = {}

        # Background monitoring task handle (set in start(); cleared in stop())
        self._monitor_task = None

        # Factory for the consensus implementation (default: RaftConsensus).
        # Injected via __init__ so callers/tests can substitute a real
        # alternate consensus without patching module globals.
        self._consensus_factory = consensus_factory or RaftConsensus

        logger.info(f"Distributed Cortex Core initialized: {node_id}")

    async def start(self):
        """Start distributed node."""
        try:
            # Initialize consensus via the configured factory.
            self.consensus = self._consensus_factory(
                node_id=self.node_id, peers=self.peers
            )

            # Initialize coordinator
            self.coordinator = DistributedCoordinator(
                node_id=self.node_id, peers=self.peers
            )

            # Join cluster
            if self.bootstrap_node:
                await self.coordinator.join(self.bootstrap_node)
            else:
                # This is the first node
                await self.consensus.become_leader()

            # Start consensus
            await self.consensus.start()

            # Start monitoring. start() is async, so a loop is guaranteed
            # to be running here; create_task schedules the monitor on it.
            self._monitor_task = asyncio.create_task(self._monitor_cluster())

            logger.info(f"Node {self.node_id} started successfully")

        except Exception as e:
            logger.error(f"Failed to start node {self.node_id}: {e}")
            raise DistributedError(f"Node startup failed: {e}")

    async def stop(self):
        """Stop the distributed node and cancel background tasks."""
        if self._monitor_task is not None and not self._monitor_task.done():
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None

        logger.info(f"Node {self.node_id} stopped")

    async def process_distributed(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process data with distributed consensus.

        Args:
            data: Intelligence data

        Returns:
            Processing results with consensus metadata
        """
        # Check if we're the leader
        if not await self.consensus.is_leader():
            # Forward to leader
            leader = await self.consensus.get_leader()
            if leader:
                return await self._forward_to_leader(leader, data)

        # Process locally
        result = self.process(data)

        # Replicate to followers
        await self._replicate_result(data, result)

        # Add consensus metadata
        result["consensus"] = {
            "node_id": self.node_id,
            "leader": True,
            "term": self.consensus.current_term,
            "replicated": True,
        }

        return result

    async def _forward_to_leader(
        self, leader_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Forward processing request to leader."""
        try:
            # In a real implementation, this would make an RPC call
            # For now, simulate local processing
            result = self.process(data)

            result["consensus"] = {
                "node_id": self.node_id,
                "leader": False,
                "forwarded_to": leader_id,
            }

            return result

        except Exception as e:
            logger.error(f"Failed to forward to leader {leader_id}: {e}")
            raise DistributedError(f"Forwarding failed: {e}")

    async def _replicate_result(self, data: Dict[str, Any], result: Dict[str, Any]):
        """Replicate result to followers."""
        replication_tasks = []

        for peer in self.peers:
            task = self.coordinator.replicate(
                peer,
                {
                    "data": data,
                    "result": result,
                    "node_id": self.node_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )
            replication_tasks.append(task)

        # Wait for majority
        results = await asyncio.gather(*replication_tasks, return_exceptions=True)

        successful = sum(1 for r in results if not isinstance(r, Exception))

        if successful < len(self.peers) // 2 + 1:
            logger.warning(
                f"Replication failed: only {successful}/{len(self.peers)} successful"
            )

    async def _monitor_cluster(self):
        """Monitor cluster health."""
        while True:
            try:
                # Check node health
                for node_id in list(self.nodes.keys()):
                    if node_id == self.node_id:
                        continue

                    # Check if node is responsive
                    if not await self.coordinator.ping(node_id):
                        logger.warning(f"Node {node_id} is unresponsive")
                        await self._handle_node_failure(node_id)

                # Update node registry
                self.nodes = await self.coordinator.get_nodes()

                await asyncio.sleep(10)  # Check every 10 seconds

            except Exception as e:
                logger.error(f"Cluster monitoring error: {e}")
                await asyncio.sleep(30)  # Back off on error

    async def _handle_node_failure(self, node_id: str):
        """Handle node failure."""
        logger.info(f"Handling node failure: {node_id}")

        # Remove from registry
        if node_id in self.nodes:
            del self.nodes[node_id]

        # Update consensus
        await self.consensus.remove_node(node_id)

        # Log failure
        logger.warning(f"Node {node_id} failed and removed from cluster")

    async def shutdown(self):
        """Gracefully shutdown distributed node."""
        logger.info(f"Shutting down distributed node {self.node_id}")

        # Stop consensus
        if self.consensus:
            await self.consensus.stop()

        # Stop coordinator
        if self.coordinator:
            await self.coordinator.stop()

        # Call parent shutdown
        super().shutdown()

        logger.info(f"Node {self.node_id} shutdown complete")
