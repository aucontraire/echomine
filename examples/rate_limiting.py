"""Rate Limiting Example - Consumer-Side Rate Limiting for API Ingestion.

This example demonstrates how to implement consumer-side rate limiting when
processing conversations from OpenAI exports using echomine library. This is
essential when downstream APIs have rate limits (e.g., 100 requests/sec).

Rate Limiting Algorithm:
    Token Bucket Algorithm - Industry standard for rate limiting
    - Tokens refill at constant rate (requests per second)
    - Burst capacity allows temporary spikes above base rate
    - Blocks when bucket is empty (backpressure)
    - Mathematically proven to provide smooth rate limiting

Use Cases:
    - Ingesting conversations into rate-limited APIs (Elasticsearch, databases)
    - Avoiding 429 Too Many Requests errors
    - Complying with third-party API quotas
    - Smooth traffic shaping to prevent service degradation

Requirements:
    - FR-003: Streaming conversations with O(1) memory
    - T066: Demonstrate rate limiting patterns for consumers
    - CHK078: Show practical integration with rate-limited APIs

Example Usage:
    ```bash
    # Process at 10 conversations/second with burst of 20
    python examples/rate_limiting.py export.json --rate-limit 10 --burst 20 --verbose

    # Strict rate limiting (no burst, default)
    python examples/rate_limiting.py export.json --rate-limit 5

    # High throughput with large burst capacity
    python examples/rate_limiting.py export.json --rate-limit 100 --burst 200
    ```

Architecture:
    echomine.stream_conversations() (O(1) memory)
            ↓
    TokenBucketRateLimiter (smooth rate limiting)
            ↓
    Consumer (API calls, database inserts, etc.)

Key Concepts:
    - Rate: Sustained requests per second (RPS)
    - Burst: Maximum tokens in bucket (allows temporary spikes)
    - Backpressure: Automatic blocking when rate exceeded
    - Token Refill: Continuous refilling based on elapsed time
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.live import Live
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table

from echomine import Conversation, OpenAIAdapter


# =============================================================================
# Token Bucket Rate Limiter
# =============================================================================


class TokenBucketRateLimiter:
    """Token bucket algorithm for consumer-side rate limiting.

    The token bucket algorithm is a widely-used method for rate limiting that
    provides smooth traffic shaping with burst support:

    Algorithm:
        1. Bucket starts with `burst` tokens
        2. Tokens refill at `rate` tokens per second
        3. Bucket capacity capped at `burst`
        4. acquire() consumes one token, blocks if bucket empty
        5. Tokens refill based on elapsed time since last refill

    Mathematical Properties:
        - Average rate guaranteed: exactly `rate` tokens/sec over time
        - Burst tolerance: up to `burst` tokens in short period
        - Backpressure: automatic blocking when sustained rate exceeded
        - Fairness: tokens refill continuously, not in batches

    Example:
        ```python
        # Allow 10 requests/sec with burst of 20
        limiter = TokenBucketRateLimiter(rate=10.0, burst=20)

        for item in items:
            limiter.acquire()  # Blocks if rate exceeded
            process_item(item)  # Process at controlled rate
        ```

    Attributes:
        rate: Token refill rate (requests per second)
        burst: Maximum bucket capacity (allows temporary spikes)
        tokens: Current available tokens (0 to burst)
        last_refill: Last time tokens were refilled (monotonic clock)
    """

    def __init__(self, rate: float, burst: int) -> None:
        """Initialize token bucket rate limiter.

        Args:
            rate: Token refill rate in requests per second (must be > 0)
            burst: Maximum bucket capacity for burst handling (must be >= 1)

        Raises:
            ValueError: If rate <= 0 or burst < 1

        Example:
            ```python
            # Strict rate limiting (no burst)
            limiter = TokenBucketRateLimiter(rate=5.0, burst=1)

            # Moderate burst tolerance
            limiter = TokenBucketRateLimiter(rate=10.0, burst=20)

            # High burst capacity
            limiter = TokenBucketRateLimiter(rate=100.0, burst=200)
            ```
        """
        if rate <= 0:
            msg = f"Rate must be positive, got {rate}"
            raise ValueError(msg)
        if burst < 1:
            msg = f"Burst must be >= 1, got {burst}"
            raise ValueError(msg)

        self.rate = rate  # Tokens per second
        self.burst = burst  # Maximum tokens
        self.tokens = float(burst)  # Start with full bucket
        self.last_refill = time.monotonic()  # Use monotonic clock (no drift)

        # Statistics for monitoring
        self._total_acquired = 0
        self._total_wait_time = 0.0
        self._max_wait_time = 0.0

    def acquire(self, tokens: int = 1) -> None:
        """Acquire tokens from bucket, blocking if insufficient tokens available.

        This method implements the core token bucket logic:
        1. Refill tokens based on elapsed time since last refill
        2. Check if enough tokens available
        3. If not, calculate wait time and sleep
        4. Consume tokens from bucket

        Blocking Behavior:
            - Non-blocking if sufficient tokens available
            - Blocks until enough tokens refilled if bucket empty
            - Uses time.sleep() for precise timing (sub-millisecond accuracy)

        Args:
            tokens: Number of tokens to acquire (default: 1)

        Example:
            ```python
            limiter = TokenBucketRateLimiter(rate=10.0, burst=20)

            # Acquire single token (most common)
            limiter.acquire()

            # Acquire multiple tokens for batch operations
            limiter.acquire(tokens=5)
            ```

        Performance:
            - Time: O(1) - constant time regardless of rate
            - Blocks: Only when rate exceeded (smooth throttling)
            - Precision: Sub-millisecond timing using time.monotonic()
        """
        while True:
            # Refill tokens based on elapsed time
            now = time.monotonic()
            elapsed = now - self.last_refill

            # Calculate tokens to add: elapsed_time * rate
            # Example: 0.5 seconds * 10 tokens/sec = 5 tokens
            tokens_to_add = elapsed * self.rate

            # Refill bucket (capped at burst capacity)
            self.tokens = min(self.burst, self.tokens + tokens_to_add)
            self.last_refill = now

            # Check if enough tokens available
            if self.tokens >= tokens:
                # Consume tokens and return
                self.tokens -= tokens
                self._total_acquired += tokens
                return

            # Not enough tokens - calculate wait time
            tokens_needed = tokens - self.tokens
            wait_time = tokens_needed / self.rate

            # Track statistics
            self._total_wait_time += wait_time
            self._max_wait_time = max(self._max_wait_time, wait_time)

            # Sleep until tokens available
            # Using small sleep to allow interruption and reduce drift
            time.sleep(wait_time)

    def get_statistics(self) -> dict[str, Any]:
        """Get rate limiter statistics for monitoring.

        Returns:
            Dictionary with rate limiter metrics:
                - total_acquired: Total tokens acquired
                - total_wait_time: Cumulative wait time in seconds
                - max_wait_time: Maximum single wait time in seconds
                - current_tokens: Current tokens in bucket
                - utilization: Percentage of time spent waiting

        Example:
            ```python
            limiter = TokenBucketRateLimiter(rate=10.0, burst=20)
            # ... process items ...
            stats = limiter.get_statistics()
            print(f"Utilization: {stats['utilization']:.1f}%")
            ```
        """
        elapsed_total = time.monotonic() - self.last_refill + self._total_wait_time
        utilization = (self._total_wait_time / elapsed_total * 100.0) if elapsed_total > 0 else 0.0

        return {
            "total_acquired": self._total_acquired,
            "total_wait_time": self._total_wait_time,
            "max_wait_time": self._max_wait_time,
            "current_tokens": self.tokens,
            "utilization": utilization,
        }


# =============================================================================
# Mock Rate-Limited API Client
# =============================================================================


class RateLimitedAPIClient:
    """Mock API client with simulated rate limits (for demonstration).

    In production, this would be replaced with actual API clients like:
    - Elasticsearch bulk API (rate limits on indexing)
    - Database connection pools (connection limits)
    - Third-party APIs (quota enforcement)

    This mock demonstrates:
    - API call simulation with realistic latency
    - Request counting for verification
    - Batch processing patterns
    """

    def __init__(self, api_name: str = "ExampleAPI") -> None:
        """Initialize mock API client.

        Args:
            api_name: Name of API for logging purposes
        """
        self.api_name = api_name
        self.request_count = 0
        self.start_time = time.monotonic()

    def ingest_conversation(self, conversation: Conversation) -> None:  # noqa: ARG002
        """Simulate API call to ingest conversation.

        In production, this would be:
        - es_client.index(index="conversations", document=conv_dict)
        - db_session.add(ConversationModel(**conv_dict))
        - api_client.post("/conversations", json=conv_dict)

        Args:
            conversation: Conversation to ingest (unused in mock, would be used in production)
        """
        # Simulate API latency (1-5ms typical for local services)
        time.sleep(0.002)  # 2ms latency
        self.request_count += 1

    def get_actual_rate(self) -> float:
        """Calculate actual request rate achieved.

        Returns:
            Actual requests per second (RPS) achieved

        Example:
            ```python
            client = RateLimitedAPIClient()
            # ... process items ...
            actual_rps = client.get_actual_rate()
            print(f"Achieved {actual_rps:.1f} req/sec")
            ```
        """
        elapsed = time.monotonic() - self.start_time
        if elapsed == 0:
            return 0.0
        return self.request_count / elapsed


# =============================================================================
# Rate-Limited Ingestion Pipeline
# =============================================================================


class RateLimitedIngestionPipeline:
    """Stream conversations from OpenAI export with rate limiting.

    This pipeline demonstrates the recommended pattern for ingesting
    conversations into rate-limited APIs:

    1. Stream conversations from export (O(1) memory via echomine)
    2. Apply rate limiter before API calls
    3. Track progress and statistics
    4. Report actual vs. target rate compliance

    Memory Complexity:
        - echomine streaming: O(1) for file size
        - Rate limiter: O(1) state
        - Total: O(1), independent of export file size

    Rate Limiting Guarantee:
        - Average rate: Exactly `rate` req/sec over time
        - Burst handling: Up to `burst` requests in short period
        - Backpressure: Automatic blocking when rate exceeded
    """

    def __init__(
        self,
        api_client: RateLimitedAPIClient,
        rate_limiter: TokenBucketRateLimiter,
        verbose: bool = False,
    ) -> None:
        """Initialize rate-limited ingestion pipeline.

        Args:
            api_client: API client for ingesting conversations
            rate_limiter: Token bucket rate limiter
            verbose: Enable detailed progress logging
        """
        self.client = api_client
        self.limiter = rate_limiter
        self.verbose = verbose

        # Statistics
        self.total_processed = 0
        self.total_skipped = 0
        self.start_time = datetime.now(UTC)

    def ingest_from_export(
        self,
        export_path: Path,
        console: Console,
    ) -> None:
        """Stream conversations from export with rate limiting.

        This is the main entry point for the pipeline. It demonstrates:
        1. Streaming conversations (O(1) memory)
        2. Rate limiting each API call
        3. Progress visualization with Rich
        4. Statistics reporting

        Args:
            export_path: Path to OpenAI export JSON file
            console: Rich console for progress display

        Raises:
            FileNotFoundError: If export file doesn't exist
            ParseError: If export JSON is malformed

        Example:
            ```python
            pipeline = RateLimitedIngestionPipeline(client, limiter, verbose=True)
            console = Console()
            pipeline.ingest_from_export(Path("export.json"), console)
            ```
        """
        # Initialize echomine adapter (stateless, lightweight)
        adapter = OpenAIAdapter()

        # Setup Rich progress display
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TextColumn("Rate:"),
            TextColumn("[cyan]{task.fields[rate]:.1f} req/s"),
            TimeElapsedColumn(),
            console=console,
        )

        with Live(progress, console=console, refresh_per_second=4):
            task = progress.add_task(
                "Processing conversations",
                total=None,  # Unknown total (streaming)
                rate=0.0,
            )

            try:
                # Stream conversations with rate limiting
                for conversation in adapter.stream_conversations(export_path):
                    # Rate limiter: acquire token (blocks if rate exceeded)
                    # This is the KEY LINE - ensures we don't exceed rate limit
                    self.limiter.acquire()

                    # Process conversation (API call)
                    self.client.ingest_conversation(conversation)
                    self.total_processed += 1

                    # Update progress display
                    actual_rate = self.client.get_actual_rate()
                    progress.update(
                        task,
                        completed=self.total_processed,
                        rate=actual_rate,
                    )

            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted by user[/yellow]")
                raise

        # Print summary statistics
        self._print_summary(console)

    def _print_summary(self, console: Console) -> None:
        """Print ingestion summary with rate limiter statistics.

        Args:
            console: Rich console for formatted output
        """
        elapsed = (datetime.now(UTC) - self.start_time).total_seconds()
        actual_rate = self.client.get_actual_rate()
        limiter_stats = self.limiter.get_statistics()

        # Create summary table
        table = Table(title="Rate-Limited Ingestion Summary", show_header=True)
        table.add_column("Metric", style="cyan", justify="right")
        table.add_column("Value", style="green")

        # Processing statistics
        table.add_row("Total Processed", str(self.total_processed))
        table.add_row("Elapsed Time", f"{elapsed:.2f}s")
        table.add_row("Target Rate", f"{self.limiter.rate:.1f} req/s")
        table.add_row("Actual Rate", f"{actual_rate:.1f} req/s")

        # Calculate compliance percentage
        if self.limiter.rate > 0:
            compliance = (actual_rate / self.limiter.rate) * 100
            table.add_row("Rate Compliance", f"{compliance:.1f}%")

        # Rate limiter statistics
        table.add_row("", "")  # Separator
        table.add_row("Total Wait Time", f"{limiter_stats['total_wait_time']:.2f}s")
        table.add_row("Max Wait Time", f"{limiter_stats['max_wait_time'] * 1000:.1f}ms")
        table.add_row("Limiter Utilization", f"{limiter_stats['utilization']:.1f}%")
        table.add_row("Current Tokens", f"{limiter_stats['current_tokens']:.1f}")

        console.print("\n")
        console.print(table)
        console.print("\n")

        # Interpretation guidance
        high_utilization_threshold = 80.0
        if limiter_stats["utilization"] > high_utilization_threshold:
            console.print(
                "[yellow]High utilization (>80%) indicates rate limit is actively "
                "constraining throughput.[/yellow]"
            )
        else:
            console.print(
                "[green]Low utilization indicates rate limit is not constraining "
                "(processing is slower than limit).[/green]"
            )


# =============================================================================
# CLI Entry Point
# =============================================================================


def main() -> None:
    """CLI entry point for rate-limited ingestion example."""
    parser = argparse.ArgumentParser(
        description="Process OpenAI conversations with rate limiting",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process at 10 conversations/second with burst of 20
  python examples/rate_limiting.py export.json --rate-limit 10 --burst 20

  # Strict rate limiting (no burst)
  python examples/rate_limiting.py export.json --rate-limit 5

  # High throughput with verbose logging
  python examples/rate_limiting.py export.json --rate-limit 100 --burst 200 --verbose

Use Cases:
  - Ingesting into Elasticsearch (rate-limited bulk API)
  - Database inserts with connection pool limits
  - Third-party API calls with quota enforcement
  - Smooth traffic shaping to prevent service degradation

Rate Limiter Algorithm:
  Token Bucket - Industry standard for smooth rate limiting
  - Tokens refill at constant rate (requests per second)
  - Burst capacity allows temporary spikes above base rate
  - Blocks when bucket is empty (automatic backpressure)
        """,
    )

    parser.add_argument(
        "export_file",
        type=Path,
        help="Path to OpenAI export JSON file",
    )

    parser.add_argument(
        "--rate-limit",
        type=float,
        required=True,
        help="Maximum requests per second (RPS) to allow",
    )

    parser.add_argument(
        "--burst",
        type=int,
        default=None,
        help="Burst capacity (max tokens in bucket). Default: same as rate limit (no burst)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose progress logging",
    )

    args = parser.parse_args()

    # Validate export file exists
    console = Console(stderr=True)
    if not args.export_file.exists():
        console.print(f"[red]Error: Export file not found: {args.export_file}[/red]")
        sys.exit(1)

    # Validate rate limit
    if args.rate_limit <= 0:
        console.print(f"[red]Error: Rate limit must be positive, got {args.rate_limit}[/red]")
        sys.exit(1)

    # Set burst capacity (default: same as rate limit for no burst)
    burst = args.burst if args.burst is not None else int(args.rate_limit)
    if burst < 1:
        console.print(f"[red]Error: Burst must be >= 1, got {burst}[/red]")
        sys.exit(1)

    # Console already initialized above for error reporting

    console.print("\n[bold cyan]Rate-Limited Ingestion Pipeline[/bold cyan]")
    console.print(f"Export File: {args.export_file}")
    console.print(f"Rate Limit: {args.rate_limit:.1f} req/s")
    console.print(f"Burst Capacity: {burst} tokens")
    console.print(f"Verbose: {args.verbose}\n")

    # Initialize rate limiter
    try:
        rate_limiter = TokenBucketRateLimiter(
            rate=args.rate_limit,
            burst=burst,
        )
    except ValueError as e:
        console.print(f"[red]Error: Invalid rate limiter configuration: {e}[/red]")
        sys.exit(1)

    # Initialize mock API client
    api_client = RateLimitedAPIClient(api_name="ExampleAPI")

    # Create ingestion pipeline
    pipeline = RateLimitedIngestionPipeline(
        api_client=api_client,
        rate_limiter=rate_limiter,
        verbose=args.verbose,
    )

    # Run ingestion
    try:
        pipeline.ingest_from_export(args.export_file, console)
    except KeyboardInterrupt:
        console.print("\n[yellow]Ingestion cancelled by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[red]Ingestion failed: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
