"""
Main Cortex Core implementation.
"""

import logging
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from cortex_core.exceptions import (
    ConfigurationError, SecurityError
)
from cortex_core.cognitive.intuition.engine import IntuitionEngine
from cortex_core.cognitive.logic.engine import LogicEngine
from cortex_core.cognitive.fusion.controller import FusionController
from cortex_core.cognitive.executive.controller import ExecutiveController
from cortex_core.cognitive.memory.system import MemorySystem
from cortex_core.security.layer import SecurityLayer
from cortex_core.monitoring.health import HealthMonitor

# Universal Enterprise Integrations
from cortex_core.integration.universal import integration_manager, AlertSeverity
from cortex_core.integration.logging import enterprise_logger, EnterpriseLogger

logger = logging.getLogger(__name__)


@dataclass
class ProcessingMetrics:
    """Metrics for intelligence processing."""
    start_time: float
    end_time: Optional[float] = None
    success: bool = False
    error: Optional[str] = None
    component_times: Dict[str, float] = None

    def __post_init__(self):
        if self.component_times is None:
            self.component_times = {}

    @property
    def duration(self) -> float:
        if self.end_time is None:
            return 0.0
        return self.end_time - self.start_time


class CortexCore:
    """
    Main Cortex Core orchestrator.

    Coordinates cognitive modules for intelligence processing.
    """

    def __init__(self, config: Dict[str, Any],
                 security_key: Optional[str] = None):
        """
        Initialize Cortex Core.

        Args:
            config: Configuration dictionary
            security_key: Optional security key for encryption
        """
        self.config = self._validate_config(config)
        self.security_key = security_key
        self.start_time = time.perf_counter()

        # Initialize enterprise logging
        self._init_enterprise_logging()

        # Initialize components
        self._init_components()

        # Initialize universal enterprise integrations
        self._init_enterprise_integrations()

        # Initialize monitoring
        self.metrics = []
        self.max_metrics = 1000

        # Log initialization with enterprise logger
        enterprise_logger.log_operation(
            operation="cortex_core_initialization",
            component="cortex_core",
            status_code=200,
            extra={"mode": self.config['system']['mode']}
        )

    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize configuration."""
        required_sections = ['system', 'security']

        for section in required_sections:
            if section not in config:
                raise ConfigurationError(
                    f"Missing required config section: {section}")

        # Set defaults
        config.setdefault('system', {}).setdefault('mode', 'adaptive')
        config.setdefault('system', {}).setdefault('log_level', 'INFO')

        # Validate mode
        valid_modes = ['adaptive', 'conservative', 'aggressive']
        mode = config['system']['mode']
        if mode not in valid_modes:
            raise ConfigurationError(
                f"Invalid mode '{mode}'. Must be one of: {valid_modes}"
            )

        return config

    def _init_enterprise_logging(self):
        """Initialize enterprise logging system."""
        # Configure enterprise logger with our config
        global enterprise_logger
        enterprise_logger = EnterpriseLogger(
            service="cortex-core-enterprise",
            environment=self.config.get('system', {}).get('environment', 'production'),
            config=self.config
        )

    def _init_enterprise_integrations(self):
        """Initialize universal enterprise integrations."""
        integration_config = self.config.get('integration', {})

        if integration_config.get('enabled', True):
            # Configure integrations from config
            integration_manager.configure_from_config(integration_config)

            # Start background export if enabled
            if integration_config.get('export_interval', 0) > 0:
                integration_manager.start_background_export(
                    interval=integration_config['export_interval']
                )

    def _init_components(self):
        """Initialize all cognitive components."""
        try:
            # Security layer
            self.security = SecurityLayer(
                master_key=self.security_key,
                config=self.config.get('security', {})
            )

            # Cognitive modules
            self.intuition = IntuitionEngine(
                config=self.config.get('intuition', {})
            )

            self.logic = LogicEngine(
                config=self.config.get('logic', {})
            )

            self.fusion = FusionController(
                config=self.config.get('fusion', {})
            )

            self.executive = ExecutiveController(
                config=self.config.get('executive', {})
            )

            self.memory = MemorySystem(
                config=self.config.get('memory', {})
            )

            # Monitoring
            self.health_monitor = HealthMonitor(
                check_interval=self.config.get('monitoring', {}).get(
                    'check_interval', 30)
            )

        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise ConfigurationError(f"Component initialization failed: {e}")

    def process(self, data: Dict[str, Any],
                validate: bool = True) -> Dict[str, Any]:
        """
        Process intelligence data through the cognitive pipeline.

        Args:
            data: Intelligence data to process
            validate: Whether to validate input data

        Returns:
            Processing results

        Raises:
            SecurityError: If validation fails
            ProcessingError: If processing fails
        """
        metrics = ProcessingMetrics(start_time=time.perf_counter(), success=False)

        # Create correlation logger for this request
        correlation_logger = enterprise_logger.create_correlation_logger(
            correlation_id=data.get('correlation_id', f"req-{int(time.perf_counter())}")
        )

        try:
            correlation_logger.log_operation(
                operation="intelligence_processing_start",
                component="cortex_core",
                extra={"data_type": data.get('type', 'unknown')}
            )

            # Record processing start metric
            integration_manager.record_metric(
                name="cortex_processing_started",
                value=1,
                tags={"component": "cortex_core", "data_type": data.get('type', 'unknown')}
            )

            # 1. Security validation
            if validate:
                validated_data = self.security.validate(data)
                if not validated_data.get('valid', False):
                    raise SecurityError(
                        f"Validation failed: {validated_data.get('errors')}")

            # 2. Intuitive processing (right hemisphere)
            intuition_start = time.perf_counter()
            intuitive_results = self.intuition.process(data)
            intuition_duration = time.perf_counter() - intuition_start
            metrics.component_times['intuition'] = intuition_duration

            # Record intuition metrics
            integration_manager.record_metric(
                name="cortex_intuition_duration",
                value=intuition_duration,
                tags={"component": "intuition"}
            )

            # 3. Logical processing (left hemisphere)
            logic_start = time.perf_counter()
            logical_results = self.logic.analyze(data)
            logic_duration = time.perf_counter() - logic_start
            metrics.component_times['logic'] = logic_duration

            # Record logic metrics
            integration_manager.record_metric(
                name="cortex_logic_duration",
                value=logic_duration,
                tags={"component": "logic"}
            )

            # 4. Neural-symbolic fusion
            fusion_start = time.perf_counter()
            fused_results = self.fusion.fuse(
                intuitive_results, logical_results)
            fusion_duration = time.perf_counter() - fusion_start
            metrics.component_times['fusion'] = fusion_duration

            # Record fusion metrics
            integration_manager.record_metric(
                name="cortex_fusion_duration",
                value=fusion_duration,
                tags={"component": "fusion"}
            )

            # 5. Executive decision making
            executive_start = time.perf_counter()
            decision = self.executive.decide(fused_results)
            executive_duration = time.perf_counter() - executive_start
            metrics.component_times['executive'] = executive_duration

            # Record executive metrics
            integration_manager.record_metric(
                name="cortex_executive_duration",
                value=executive_duration,
                tags={"component": "executive"}
            )

            # 6. Memory storage
            memory_start = time.perf_counter()
            memory_id = self.memory.store({
                'data': data,
                'intuitive': intuitive_results,
                'logical': logical_results,
                'fused': fused_results,
                'decision': decision,
                'timestamp': datetime.utcnow().isoformat()
            })
            memory_duration = time.perf_counter() - memory_start
            metrics.component_times['memory'] = memory_duration

            # Record memory metrics
            integration_manager.record_metric(
                name="cortex_memory_duration",
                value=memory_duration,
                tags={"component": "memory"}
            )

            # Calculate total processing time
            total_duration = time.perf_counter() - metrics.start_time

            # 7. Prepare response
            response = {
                'success': True,
                'decision': decision,
                'analysis': fused_results,
                'memory_id': memory_id,
                'processing_time': total_duration,
                'component_times': metrics.component_times,
                'correlation_id': correlation_logger.correlation_id,
                'metadata': {
                    'timestamp': datetime.utcnow().isoformat(),
                    'mode': self.config['system']['mode']
                }
            }

            # 8. Update metrics
            metrics.end_time = time.perf_counter()
            metrics.success = True
            self._record_metrics(metrics)

            # Record success metrics
            integration_manager.record_metric(
                name="cortex_processing_completed",
                value=1,
                tags={"status": "success", "data_type": data.get('type', 'unknown')}
            )
            integration_manager.record_metric(
                name="cortex_processing_duration",
                value=total_duration,
                tags={"component": "cortex_core"}
            )

            correlation_logger.log_operation(
                operation="intelligence_processing_complete",
                component="cortex_core",
                duration_ms=total_duration * 1000,
                status_code=200,
                extra={"decision": decision.get('action', 'unknown')}
            )

            return response

        except Exception as e:
            metrics.end_time = time.perf_counter()
            metrics.error = str(e)
            self._record_metrics(metrics)

            # Calculate failure duration
            failure_duration = time.perf_counter() - metrics.start_time

            # Record failure metrics and alert
            integration_manager.record_metric(
                name="cortex_processing_failed",
                value=1,
                tags={"error_type": type(e).__name__, "component": "cortex_core"}
            )

            # Send alert for processing failure
            integration_manager.record_alert(
                title="Cortex Core Processing Failure",
                description=f"Intelligence processing failed: {str(e)}",
                severity=AlertSeverity.ERROR,
                source="cortex_core",
                tags={
                    "error_type": type(e).__name__,
                    "data_type": data.get('type', 'unknown'),
                    "component": "cortex_core"
                },
                runbook_url="https://docs.cortex-core.com/troubleshooting/processing-failures"
            )

            # Log error with enterprise logger
            correlation_logger.log_error(
                error=e,
                component="cortex_core",
                extra={
                    "data_type": data.get('type', 'unknown'),
                    "processing_duration": failure_duration
                }
            )

            # Return error response
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__,
                'processing_time': failure_duration,
                'correlation_id': correlation_logger.correlation_id,
                'timestamp': datetime.utcnow().isoformat()
            }

    def _record_metrics(self, metrics: ProcessingMetrics):
        """Record processing metrics."""
        self.metrics.append(metrics)

        # Limit metrics history
        if len(self.metrics) > self.max_metrics:
            self.metrics = self.metrics[-self.max_metrics:]

    def get_status(self) -> Dict[str, Any]:
        """Get system status."""
        return {
            'status': 'operational',
            'version': '3.0.0',
            'mode': self.config['system']['mode'],
            'components': {
                'security': self.security.is_healthy(),
                'intuition': self.intuition.is_healthy(),
                'logic': self.logic.is_healthy(),
                'fusion': self.fusion.is_healthy(),
                'executive': self.executive.is_healthy(),
                'memory': self.memory.is_healthy()
            },
            'metrics': {
                'total_processed': len(self.metrics),
                'success_rate': self._calculate_success_rate(),
                'avg_processing_time': self._calculate_avg_processing_time()
            }
        }

    def _calculate_success_rate(self) -> float:
        """Calculate success rate from metrics."""
        if not self.metrics:
            return 0.0

        successful = sum(1 for m in self.metrics if m.success)
        return successful / len(self.metrics)

    def _calculate_avg_processing_time(self) -> float:
        """Calculate average processing time."""
        if not self.metrics:
            return 0.0

        total_time = sum(m.duration for m in self.metrics)
        return total_time / len(self.metrics)

    def shutdown(self):
        """Gracefully shutdown Cortex Core."""
        logger.info("Shutting down Cortex Core...")

        # Shutdown components in reverse order
        self.health_monitor.stop()
        self.memory.shutdown()

        logger.info("Cortex Core shutdown complete")
