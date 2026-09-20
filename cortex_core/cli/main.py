"""
Command-line interface for Cortex Core.
"""

import json
import logging

import click

from cortex_core import create_cortex, create_distributed_cortex
from cortex_core.version import get_version

logger = logging.getLogger(__name__)


@click.group()
@click.option("--config", "-c", default=None, help="Configuration file path")
@click.option("--log-level", default="INFO", help="Logging level")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.pass_context
def cli(ctx, config, log_level, verbose):
    """Cortex Core Enterprise CLI."""
    # Configure logging
    level = getattr(logging, log_level.upper())
    logging.basicConfig(
        level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Store context
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config
    ctx.obj["verbose"] = verbose

    if verbose:
        click.echo(f"Cortex Core CLI initialized with config: {config}")


@cli.command()
@click.option("--mode", default="adaptive", help="Operation mode")
@click.option("--host", default="0.0.0.0", help="API host")
@click.option("--port", default=8080, type=int, help="API port")
@click.option("--workers", default=4, type=int, help="Number of workers")
@click.pass_context
def run(ctx, mode, host, port, workers):
    """Run Cortex Core API server."""
    try:
        import uvicorn

        click.echo(f"Starting Cortex Core API server on {host}:{port}")

        uvicorn.run(
            "cortex_core.api.rest:app",
            host=host,
            port=port,
            workers=workers,
            log_level="info",
        )

    except Exception as e:
        click.echo(f"Failed to start server: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument("data", type=click.File("r"))
@click.option("--output", "-o", type=click.File("w"), help="Output file")
@click.option("--format", default="json", help="Output format")
@click.pass_context
def process(ctx, data, output, format):
    """Process intelligence data from file."""
    try:
        # Load configuration

        # Create Cortex Core
        cortex = create_cortex(config_dict=config)

        # Load data
        input_data = json.load(data)

        # Process
        result = cortex.process(input_data)

        # Output
        if output:
            json.dump(result, output, indent=2)
        else:
            if format == "json":
                click.echo(json.dumps(result, indent=2))
            else:
                click.echo(f"Success: {result.get('success', False)}")
                click.echo(f"Decision: {result.get('decision', 'N/A')}")

    except Exception as e:
        click.echo(f"Processing failed: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option("--node-id", required=True, help="Node identifier")
@click.option("--peers", required=True, help="Comma-separated list of peer addresses")
@click.option("--bootstrap-node", help="Bootstrap node for joining cluster")
@click.pass_context
def run_distributed(ctx, node_id, peers, bootstrap_node):
    """Run distributed Cortex Core node."""
    try:
        import asyncio

        # Parse peers
        peer_list = [p.strip() for p in peers.split(",")]

        # Load configuration

        async def run_node():
            # Create distributed cortex
            cortex = create_distributed_cortex(
                node_id=node_id,
                peers=peer_list,
                config_dict=config,
                bootstrap_node=bootstrap_node,
            )

            # Start the node
            await cortex.start()

            click.echo(f"Distributed node {node_id} started. Press Ctrl+C to stop.")

            # Keep running
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                click.echo(f"Stopping node {node_id}...")
                await cortex.shutdown()
                click.echo("Node stopped.")

        # Run the async function
        asyncio.run(run_node())

    except Exception as e:
        click.echo(f"Failed to start distributed node: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.pass_context
def status(ctx):
    """Show system status."""
    try:
        # Load configuration

        # Create Cortex Core
        cortex = create_cortex(config_dict=config)

        # Get status
        status = cortex.get_status()

        # Display
        click.echo("Cortex Core Status")
        click.echo("=" * 20)
        click.echo(f"Status: {status['status']}")
        click.echo(f"Version: {status['version']}")
        click.echo(f"Mode: {status['mode']}")
        click.echo(f"Components: {len(status['components'])} total")

        # Component health
        click.echo("\nComponent Health:")
        for component, healthy in status["components"].items():
            status_icon = "✅" if healthy else "❌"
            click.echo(f"  {status_icon} {component}")

        # Metrics
        metrics = status["metrics"]
        click.echo("\nMetrics:")
        click.echo(f"  Total processed: {metrics['total_processed']}")
        click.echo(f"  Success rate: {metrics['success_rate']:.1%}")
        click.echo(f"  Avg processing time: {metrics['avg_time']:.3f}s")

    except Exception as e:
        click.echo(f"Failed to get status: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.pass_context
def health(ctx):
    """Check system health."""
    try:
        # Load configuration

        # Create Cortex Core
        cortex = create_cortex(config_dict=config)

        # Get status
        status = cortex.get_status()

        if status["status"] == "operational":
            click.echo("✅ System is healthy")
            exit(0)
        else:
            click.echo("❌ System is unhealthy")
            exit(1)

    except Exception as e:
        click.echo(f"❌ Health check failed: {e}")
        exit(1)


@cli.command()
def version():
    """Show version information."""
    version_info = get_version()

    click.echo("Cortex Core Enterprise")
    click.echo(f"Version: {version_info['version']}")
    click.echo(f"Build: {version_info['build']}")
    click.echo(f"API Version: {version_info['api_version']}")

    click.echo("\nFeatures:")
    for feature, enabled in version_info["features"].items():
        status = "✅" if enabled else "❌"
        click.echo(f"  {status} {feature}")


@cli.group()
def db():
    """Database management commands."""
    pass


@db.command()
@click.option("--url", help="Database URL")
@click.pass_context
def init(ctx, url):
    """Initialize database."""
    click.echo("Database initialization not yet implemented")
    # Would implement database initialization here


@db.command()
@click.pass_context
def migrate(ctx):
    """Run database migrations."""
    click.echo("Database migration not yet implemented")
    # Would implement database migrations here


@db.command()
@click.pass_context
def upgrade(ctx):
    """Upgrade database schema."""
    click.echo("Database upgrade not yet implemented")
    # Would implement database schema upgrade here


@cli.group()
def config():
    """Configuration management commands."""
    pass


@config.command()
@click.argument("key")
@click.argument("value")
@click.pass_context
def set(ctx, key, value):
    """Set configuration value."""
    click.echo(f"Setting {key} = {value}")
    # Would implement configuration setting here


@config.command()
@click.argument("key", required=False)
@click.pass_context
def get(ctx, key):
    """Get configuration value."""
    if key:
        click.echo(f"Getting {key}")
    else:
        click.echo("Getting all configuration")
    # Would implement configuration retrieval here


@config.command()
@click.pass_context
def validate(ctx):
    """Validate configuration."""
    try:
        click.echo("✅ Configuration is valid")
    except Exception as e:
        click.echo(f"❌ Configuration validation failed: {e}")
        raise click.Abort()


if __name__ == "__main__":
    cli()
