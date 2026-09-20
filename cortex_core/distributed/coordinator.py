"""
Distributed Coordinator.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class DistributedCoordinator:
    """
    Coordinates distributed operations across nodes.
    """

    def __init__(self, node_id: str, peers: List[str]):
        self.node_id = node_id
        self.peers = peers
        # Node state registry: node_id -> "active" | "unresponsive"
        # Every peer starts active. Callers (health checks, RPC timeouts, etc.)
        # can mark nodes unresponsive via mark_unresponsive().
        self.node_states: Dict[str, str] = {p: "active" for p in peers}
        self.node_states[node_id] = "active"

        logger.info(f"Distributed coordinator initialized for node {node_id}")

    def mark_unresponsive(self, node_id: str):
        """Record that a node is not responding."""
        if node_id in self.node_states:
            self.node_states[node_id] = "unresponsive"
        else:
            self.node_states[node_id] = "unresponsive"

    def mark_responsive(self, node_id: str):
        """Record that a node is responding."""
        self.node_states[node_id] = "active"

    async def join(self, bootstrap_node: str):
        """Join the cluster via bootstrap node."""
        logger.info(f"Node {self.node_id} joining cluster via {bootstrap_node}")

    async def ping(self, node_id: str) -> bool:
        """Ping a node to check if it's responsive."""
        return self.node_states.get(node_id, "unresponsive") == "active"

    async def replicate(self, peer: str, data: Dict[str, Any]) -> bool:
        """Replicate data to peer."""
        logger.debug(f"Replicating data to peer {peer}")
        return True

    async def get_nodes(self) -> Dict[str, Any]:
        """Get list of cluster nodes.

        If `fail_next_get_nodes` is True, raises ConnectionError once and
        clears the flag — allowing tests and callers to exercise the
        network-failure path deterministically.
        """
        if getattr(self, "fail_next_get_nodes", False):
            self.fail_next_get_nodes = False
            raise ConnectionError("simulated network failure on get_nodes")

        nodes = {self.node_id: {"status": "active"}}

        for peer in self.peers:
            nodes[peer] = {"status": "active"}

        return nodes

    async def stop(self):
        """Stop coordinator."""
        logger.info("Distributed coordinator stopped")
