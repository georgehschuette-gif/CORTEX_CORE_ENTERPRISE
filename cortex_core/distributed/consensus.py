"""
Raft Consensus implementation.
"""

import logging
from typing import List

logger = logging.getLogger(__name__)


class RaftConsensus:
    """
    Simplified Raft consensus algorithm implementation.
    """

    def __init__(self, node_id: str, peers: List[str]):
        self.node_id = node_id
        self.peers = peers
        self.current_term = 0
        self.voted_for = None
        self.state = "follower"  # follower, candidate, leader

        logger.info(f"Raft consensus initialized for node {node_id}")

    async def start(self):
        """Start consensus protocol."""
        logger.info("Raft consensus started")

    async def stop(self):
        """Stop consensus protocol."""
        logger.info("Raft consensus stopped")

    async def is_leader(self) -> bool:
        """Check if this node is the leader."""
        return self.state == "leader"

    async def get_leader(self) -> str:
        """Get current leader node ID."""
        # Simplified - return first peer
        return self.peers[0] if self.peers else self.node_id

    async def become_leader(self):
        """Become the leader."""
        self.state = "leader"
        logger.info(f"Node {self.node_id} became leader")

    async def remove_node(self, node_id: str):
        """Remove node from cluster."""
        if node_id in self.peers:
            self.peers.remove(node_id)
            logger.info(f"Node {node_id} removed from cluster")
