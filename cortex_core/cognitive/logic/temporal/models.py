"""
Temporal reasoning models.
"""

from datetime import datetime
from typing import Any, Dict, List


class TemporalReasoner:
    """
    Temporal reasoning for understanding time-based patterns and causality.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def analyze_temporal_patterns(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze temporal patterns in events.

        Args:
            events: List of timestamped events

        Returns:
            Temporal analysis results
        """
        if not events:
            return {"patterns": [], "correlations": []}

        # Sort events by time
        sorted_events = sorted(events, key=lambda x: x.get("timestamp", ""))

        # Find patterns
        patterns = self._identify_patterns(sorted_events)

        # Analyze correlations
        correlations = self._analyze_correlations(sorted_events)

        # Predict next events
        predictions = self._predict_next_events(sorted_events)

        return {
            "patterns": patterns,
            "correlations": correlations,
            "predictions": predictions,
            "event_count": len(events),
            "time_span": self._calculate_time_span(sorted_events),
        }

    def _identify_patterns(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify temporal patterns."""
        patterns = []

        # Look for periodic patterns
        if len(events) >= 3:
            intervals = []
            for i in range(1, len(events)):
                if "timestamp" in events[i] and "timestamp" in events[i - 1]:
                    try:
                        t1 = datetime.fromisoformat(
                            events[i - 1]["timestamp"].replace("Z", "+00:00")
                        )
                        t2 = datetime.fromisoformat(
                            events[i]["timestamp"].replace("Z", "+00:00")
                        )
                        interval = (t2 - t1).total_seconds()
                        intervals.append(interval)
                    except BaseException:
                        continue

            if intervals:
                avg_interval = sum(intervals) / len(intervals)
                if avg_interval > 0:
                    patterns.append(
                        {
                            "type": "periodic",
                            "average_interval_seconds": avg_interval,
                            "confidence": 0.8 if len(intervals) > 5 else 0.5,
                        }
                    )

        # Look for clusters
        if len(events) >= 5:
            # Simple clustering by time proximity
            clusters = self._find_time_clusters(events)
            if clusters:
                patterns.append(
                    {
                        "type": "clustered",
                        "cluster_count": len(clusters),
                        "average_cluster_size": sum(len(c) for c in clusters)
                        / len(clusters),
                    }
                )

        return patterns

    def _analyze_correlations(
        self, events: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Analyze correlations between events."""
        correlations = []

        # Simple correlation analysis
        event_types = {}
        for event in events:
            event_type = event.get("type", "unknown")
            timestamp = event.get("timestamp")

            if timestamp:
                if event_type not in event_types:
                    event_types[event_type] = []
                event_types[event_type].append(timestamp)

        # Look for co-occurring event types
        type_pairs = []
        for type1 in event_types:
            for type2 in event_types:
                if type1 != type2:
                    pair = tuple(sorted([type1, type2]))
                    if pair not in type_pairs:
                        type_pairs.append(pair)
                        correlation = self._calculate_type_correlation(
                            event_types[type1], event_types[type2]
                        )
                        if abs(correlation) > 0.3:
                            correlations.append(
                                {
                                    "types": list(pair),
                                    "correlation": correlation,
                                    "strength": (
                                        "strong"
                                        if abs(correlation) > 0.7
                                        else "moderate"
                                    ),
                                }
                            )

        return correlations

    def _predict_next_events(
        self, events: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Predict next events based on patterns."""
        predictions = []

        if len(events) < 3:
            return predictions

        # Simple linear extrapolation
        try:
            timestamps = []
            for event in events[-10:]:  # Last 10 events
                if "timestamp" in event:
                    try:
                        ts = datetime.fromisoformat(
                            event["timestamp"].replace("Z", "+00:00")
                        )
                        timestamps.append(ts.timestamp())
                    except BaseException:
                        continue

            if len(timestamps) >= 3:
                # Calculate trend
                time_diffs = []
                for i in range(1, len(timestamps)):
                    time_diffs.append(timestamps[i] - timestamps[i - 1])

                avg_interval = sum(time_diffs) / len(time_diffs)
                next_timestamp = timestamps[-1] + avg_interval

                predictions.append(
                    {
                        "type": "next_event",
                        "predicted_time": datetime.fromtimestamp(
                            next_timestamp
                        ).isoformat(),
                        "confidence": 0.6,
                        "based_on_events": len(timestamps),
                    }
                )

        except Exception:
            # If prediction fails, return empty
            pass

        return predictions

    def _calculate_time_span(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate the time span of events."""
        if not events:
            return {"start": None, "end": None, "duration_seconds": 0}

        timestamps = []
        for event in events:
            if "timestamp" in event:
                try:
                    ts = datetime.fromisoformat(
                        event["timestamp"].replace("Z", "+00:00")
                    )
                    timestamps.append(ts)
                except BaseException:
                    continue

        if not timestamps:
            return {"start": None, "end": None, "duration_seconds": 0}

        start = min(timestamps)
        end = max(timestamps)
        duration = (end - start).total_seconds()

        return {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "duration_seconds": duration,
        }

    def _find_time_clusters(
        self, events: List[Dict[str, Any]], threshold_seconds: int = 3600
    ) -> List[List[Dict[str, Any]]]:
        """Find clusters of events close in time."""
        clusters = []

        current_cluster = []
        last_time = None

        for event in events:
            if "timestamp" in event:
                try:
                    event_time = datetime.fromisoformat(
                        event["timestamp"].replace("Z", "+00:00")
                    )

                    if (
                        last_time
                        and (event_time - last_time).total_seconds() > threshold_seconds
                    ):
                        # Start new cluster
                        if current_cluster:
                            clusters.append(current_cluster)
                        current_cluster = [event]
                    else:
                        current_cluster.append(event)

                    last_time = event_time

                except BaseException:
                    continue

        if current_cluster:
            clusters.append(current_cluster)

        return clusters

    def _calculate_type_correlation(
        self, times1: List[str], times2: List[str]
    ) -> float:
        """Calculate correlation between two event type time series."""
        # Simple correlation based on proximity
        if not times1 or not times2:
            return 0.0

        try:
            # Convert to timestamps
            ts1 = [
                datetime.fromisoformat(t.replace("Z", "+00:00")).timestamp()
                for t in times1
            ]
            ts2 = [
                datetime.fromisoformat(t.replace("Z", "+00:00")).timestamp()
                for t in times2
            ]

            # Find closest pairs
            correlations = []
            for t1 in ts1:
                closest_t2 = min(ts2, key=lambda x: abs(x - t1))
                time_diff = abs(t1 - closest_t2)

                # Correlation based on time proximity (closer = more
                # correlated)
                # 24 hours window
                correlation = max(0, 1 - (time_diff / (24 * 3600)))
                correlations.append(correlation)

            return sum(correlations) / len(correlations) if correlations else 0.0

        except BaseException:
            return 0.0
