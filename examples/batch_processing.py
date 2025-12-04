"""Batch Processing Example - Concurrent Multi-File Export Processing.

This example demonstrates how to process multiple OpenAI export files concurrently
using echomine with thread-safe operations, progress tracking, and error isolation:

- Thread-safe concurrent processing using ThreadPoolExecutor
- Independent iterators for each file (no shared state)
- Progress tracking across all files with Rich visualization
- Graceful handling of per-file failures (don't stop all processing)
- Aggregated statistics from all files (total conversations, messages, throughput)

Requirements:
    - FR-337: Stream-based processing for memory efficiency
    - FR-338: Progress reporting for visibility
    - CHK003: Thread-safe adapter usage (stateless design)
    - CHK077: on_skip callback demonstration

Thread Safety:
    OpenAIAdapter is thread-safe because it is stateless - all state is passed
    as arguments (file_path, callbacks). Each worker thread creates independent
    iterators over different files, with no shared mutable state.

    Architecture:
        Main Thread:
          ├─ Worker Thread 1 → OpenAIAdapter.stream_conversations(file1.json)
          ├─ Worker Thread 2 → OpenAIAdapter.stream_conversations(file2.json)
          ├─ Worker Thread 3 → OpenAIAdapter.stream_conversations(file3.json)
          └─ Worker Thread 4 → OpenAIAdapter.stream_conversations(file4.json)

        Each worker has:
          - Independent file handle (context manager isolation)
          - Independent ijson parser state (no sharing)
          - Independent progress tracking (thread-local counters)

Example Usage:
    ```bash
    # Process multiple files with default workers (CPU count)
    python examples/batch_processing.py file1.json file2.json file3.json

    # Process with custom worker count and verbose logging
    python examples/batch_processing.py *.json --workers 4 --verbose

    # JSON output for pipeline composition
    python examples/batch_processing.py export1.json export2.json --json
    ```

Performance Characteristics:
    - Memory: O(workers) - each worker holds one conversation in memory
    - Throughput: ~Linear scaling with worker count (I/O bound)
    - Progress: Real-time updates from all workers via thread-safe Rich display

Error Handling:
    - Individual file failures don't stop other workers
    - Malformed conversations skipped per file (graceful degradation)
    - Final report shows success/failure status per file
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.live import Live
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table

from echomine import OpenAIAdapter


# =============================================================================
# Per-File Processing Statistics
# =============================================================================


@dataclass
class FileStats:
    """Statistics for processing a single export file.

    Tracks processing metrics for one file, including counts, timings,
    and error states. Used to aggregate results across all files.

    Attributes:
        file_path: Path to the processed export file
        conversations_processed: Number of conversations successfully parsed
        messages_processed: Total messages across all conversations
        conversations_skipped: Number of malformed conversations skipped
        success: True if file processed without fatal errors
        error_message: Error message if success=False
        elapsed_seconds: Total processing time for this file
    """

    file_path: Path
    conversations_processed: int = 0
    messages_processed: int = 0
    conversations_skipped: int = 0
    success: bool = False
    error_message: str | None = None
    elapsed_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary with all statistics fields
        """
        return {
            "file_path": str(self.file_path),
            "conversations_processed": self.conversations_processed,
            "messages_processed": self.messages_processed,
            "conversations_skipped": self.conversations_skipped,
            "success": self.success,
            "error_message": self.error_message,
            "elapsed_seconds": round(self.elapsed_seconds, 2),
        }


# =============================================================================
# Aggregated Batch Statistics
# =============================================================================


@dataclass
class BatchStats:
    """Aggregated statistics across all processed files.

    Combines per-file statistics to provide overall batch processing metrics.
    Used for final summary reporting.

    Attributes:
        files_total: Total number of files attempted
        files_successful: Number of files processed without fatal errors
        files_failed: Number of files that failed with fatal errors
        conversations_total: Total conversations processed across all files
        messages_total: Total messages processed across all files
        conversations_skipped_total: Total malformed conversations skipped
        elapsed_seconds: Total wall-clock time for entire batch
        throughput_conv_per_sec: Conversations per second throughput
    """

    files_total: int = 0
    files_successful: int = 0
    files_failed: int = 0
    conversations_total: int = 0
    messages_total: int = 0
    conversations_skipped_total: int = 0
    elapsed_seconds: float = 0.0
    throughput_conv_per_sec: float = 0.0

    @staticmethod
    def from_file_stats(file_stats: list[FileStats], elapsed: float) -> BatchStats:
        """Aggregate individual file statistics into batch summary.

        Args:
            file_stats: List of per-file statistics
            elapsed: Total wall-clock time for batch processing

        Returns:
            Aggregated BatchStats object
        """
        successful = [fs for fs in file_stats if fs.success]
        failed = [fs for fs in file_stats if not fs.success]

        total_conversations = sum(fs.conversations_processed for fs in file_stats)
        total_messages = sum(fs.messages_processed for fs in file_stats)
        total_skipped = sum(fs.conversations_skipped for fs in file_stats)

        throughput = total_conversations / elapsed if elapsed > 0 else 0.0

        return BatchStats(
            files_total=len(file_stats),
            files_successful=len(successful),
            files_failed=len(failed),
            conversations_total=total_conversations,
            messages_total=total_messages,
            conversations_skipped_total=total_skipped,
            elapsed_seconds=round(elapsed, 2),
            throughput_conv_per_sec=round(throughput, 1),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary with all batch statistics fields
        """
        return {
            "files_total": self.files_total,
            "files_successful": self.files_successful,
            "files_failed": self.files_failed,
            "conversations_total": self.conversations_total,
            "messages_total": self.messages_total,
            "conversations_skipped_total": self.conversations_skipped_total,
            "elapsed_seconds": self.elapsed_seconds,
            "throughput_conv_per_sec": self.throughput_conv_per_sec,
        }


# =============================================================================
# Worker Thread Processing Logic
# =============================================================================


def process_single_file(
    file_path: Path,
    progress: Progress,
    task_id: TaskID,
    verbose: bool = False,
) -> FileStats:
    """Process a single export file with progress tracking (worker thread entry point).

    This function is executed by a worker thread from ThreadPoolExecutor.
    It processes one file completely, tracking progress and errors independently.

    Thread Safety:
        - Creates independent OpenAIAdapter (stateless, no shared state)
        - Uses independent file handle (context manager isolation)
        - Updates thread-safe Rich Progress display via task_id
        - Returns immutable FileStats (no shared mutable state)

    Args:
        file_path: Path to OpenAI export JSON file
        progress: Rich Progress display (thread-safe)
        task_id: Progress bar ID for this file
        verbose: Enable detailed logging to stderr

    Returns:
        FileStats with processing results for this file

    Example:
        ```python
        # Called by ThreadPoolExecutor worker
        stats = process_single_file(Path("export.json"), progress, task_id)
        # Returns FileStats(conversations_processed=1000, success=True, ...)
        ```
    """
    stats = FileStats(file_path=file_path)
    start_time = datetime.now(UTC)

    # Thread-safe logging (stderr is thread-safe in Python)
    if verbose:
        print(
            f"[Worker {threading.current_thread().name}] Started processing {file_path.name}",
            file=sys.stderr,
        )

    try:
        # Initialize adapter (stateless, thread-safe)
        adapter = OpenAIAdapter()

        # Define progress callback for this file
        # Callback updates the Rich progress bar (thread-safe operation)
        def on_progress(count: int) -> None:
            """Update progress bar for this file (thread-safe)."""
            progress.update(task_id, completed=count)

        # Define skip callback for malformed conversations
        def on_skip(conversation_id: str, reason: str) -> None:
            """Track skipped conversations (thread-local state)."""
            stats.conversations_skipped += 1
            if verbose:
                print(
                    f"[Worker {threading.current_thread().name}] "
                    f"Skipped {conversation_id}: {reason}",
                    file=sys.stderr,
                )

        # Stream conversations with callbacks (FR-337, FR-338, CHK077)
        # Memory: O(1) for file size - streaming with ijson
        # Each worker processes independently, no inter-thread communication
        for conversation in adapter.stream_conversations(
            file_path,
            progress_callback=on_progress,
            on_skip=on_skip,
        ):
            # Count messages (thread-local accumulation)
            stats.messages_processed += len(conversation.messages)
            stats.conversations_processed += 1

            # Update progress bar (thread-safe Rich operation)
            progress.update(
                task_id,
                completed=stats.conversations_processed,
                description=f"[green]{file_path.name}[/green]",
            )

        # Mark as successful
        stats.success = True
        progress.update(
            task_id,
            description=f"[green]✓ {file_path.name}[/green]",
            completed=stats.conversations_processed,
        )

    except FileNotFoundError:
        stats.success = False
        stats.error_message = "File not found"
        progress.update(
            task_id,
            description=f"[red]✗ {file_path.name} (not found)[/red]",
        )

    except PermissionError:
        stats.success = False
        stats.error_message = "Permission denied"
        progress.update(
            task_id,
            description=f"[red]✗ {file_path.name} (permission denied)[/red]",
        )

    except Exception as e:
        stats.success = False
        stats.error_message = str(e)
        progress.update(
            task_id,
            description=f"[red]✗ {file_path.name} (error)[/red]",
        )
        if verbose:
            print(
                f"[Worker {threading.current_thread().name}] "
                f"Error processing {file_path.name}: {e}",
                file=sys.stderr,
            )

    # Record elapsed time
    stats.elapsed_seconds = (datetime.now(UTC) - start_time).total_seconds()

    if verbose:
        print(
            f"[Worker {threading.current_thread().name}] "
            f"Completed {file_path.name}: "
            f"{stats.conversations_processed} conversations, "
            f"{stats.messages_processed} messages, "
            f"{stats.elapsed_seconds:.2f}s",
            file=sys.stderr,
        )

    return stats


# =============================================================================
# Batch Processing Orchestrator
# =============================================================================


class BatchProcessor:
    """Orchestrate concurrent processing of multiple export files.

    Manages thread pool, progress display, and aggregates results from
    all worker threads. Ensures graceful handling of per-file failures.

    Thread Safety:
        - Uses ThreadPoolExecutor for worker thread management
        - Rich Progress display is thread-safe
        - No shared mutable state between workers
        - Results collected via Future objects

    Example:
        ```python
        processor = BatchProcessor(workers=4, verbose=True)
        batch_stats, file_stats = processor.process_files([
            Path("file1.json"),
            Path("file2.json"),
        ])
        print(f"Processed {batch_stats.conversations_total} conversations")
        ```
    """

    def __init__(self, workers: int = 4, verbose: bool = False) -> None:
        """Initialize batch processor.

        Args:
            workers: Number of worker threads (default: CPU count)
            verbose: Enable detailed logging to stderr
        """
        self.workers = workers
        self.verbose = verbose
        self.console = Console(stderr=True)  # Progress to stderr

    def process_files(self, file_paths: list[Path]) -> tuple[BatchStats, list[FileStats]]:
        """Process multiple export files concurrently.

        Creates thread pool, dispatches workers, tracks progress, and
        aggregates results. Individual file failures don't stop processing.

        Args:
            file_paths: List of export file paths to process

        Returns:
            Tuple of (batch_stats, file_stats_list)

        Example:
            ```python
            batch_stats, file_stats = processor.process_files([
                Path("export1.json"),
                Path("export2.json"),
            ])
            ```
        """
        start_time = datetime.now(UTC)

        # Create Rich progress display (thread-safe)
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total})"),
            TimeElapsedColumn(),
            console=self.console,
        )

        # Store file stats from workers
        file_stats: list[FileStats] = []

        with Live(progress, console=self.console):
            # Create progress bar for each file
            tasks = {
                file_path: progress.add_task(
                    f"[cyan]{file_path.name}[/cyan]",
                    total=100,  # Will update dynamically
                )
                for file_path in file_paths
            }

            # Create thread pool executor
            with ThreadPoolExecutor(max_workers=self.workers) as executor:
                # Submit all files to worker threads
                futures: dict[Future[FileStats], Path] = {
                    executor.submit(
                        process_single_file,
                        file_path,
                        progress,
                        task_id,
                        self.verbose,
                    ): file_path
                    for file_path, task_id in tasks.items()
                }

                # Collect results as workers complete
                for future in as_completed(futures):
                    file_path = futures[future]
                    try:
                        stats = future.result()
                        file_stats.append(stats)
                    except Exception as e:
                        # Worker thread raised unexpected exception
                        # Create failed FileStats for this file
                        file_stats.append(
                            FileStats(
                                file_path=file_path,
                                success=False,
                                error_message=f"Worker exception: {e}",
                            )
                        )
                        if self.verbose:
                            print(
                                f"[ERROR] Worker failed for {file_path.name}: {e}",
                                file=sys.stderr,
                            )

        # Calculate elapsed time
        elapsed = (datetime.now(UTC) - start_time).total_seconds()

        # Aggregate statistics
        batch_stats = BatchStats.from_file_stats(file_stats, elapsed)

        return batch_stats, file_stats


# =============================================================================
# Output Formatting
# =============================================================================


def print_summary_table(batch_stats: BatchStats, file_stats: list[FileStats]) -> None:
    """Print formatted summary table to stderr.

    Args:
        batch_stats: Aggregated batch statistics
        file_stats: Per-file statistics
    """
    console = Console(stderr=True)

    # Batch summary table
    summary_table = Table(title="Batch Processing Summary", show_header=True)
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="green")

    summary_table.add_row("Files Total", str(batch_stats.files_total))
    summary_table.add_row("Files Successful", str(batch_stats.files_successful))
    summary_table.add_row("Files Failed", str(batch_stats.files_failed))
    summary_table.add_row("Conversations Processed", str(batch_stats.conversations_total))
    summary_table.add_row("Messages Processed", str(batch_stats.messages_total))
    summary_table.add_row("Conversations Skipped", str(batch_stats.conversations_skipped_total))
    summary_table.add_row("Elapsed Time", f"{batch_stats.elapsed_seconds:.2f}s")
    summary_table.add_row("Throughput", f"{batch_stats.throughput_conv_per_sec:.1f} conv/sec")

    console.print()
    console.print(summary_table)

    # Per-file results table
    file_table = Table(title="Per-File Results", show_header=True)
    file_table.add_column("File", style="cyan")
    file_table.add_column("Status", style="bold")
    file_table.add_column("Conversations", justify="right")
    file_table.add_column("Messages", justify="right")
    file_table.add_column("Skipped", justify="right")
    file_table.add_column("Time (s)", justify="right")

    for stats in file_stats:
        status = "[green]✓ Success[/green]" if stats.success else "[red]✗ Failed[/red]"
        file_table.add_row(
            stats.file_path.name,
            status,
            str(stats.conversations_processed),
            str(stats.messages_processed),
            str(stats.conversations_skipped),
            f"{stats.elapsed_seconds:.2f}",
        )

    console.print()
    console.print(file_table)
    console.print()


def print_json_output(batch_stats: BatchStats, file_stats: list[FileStats]) -> None:
    """Print JSON output to stdout.

    Args:
        batch_stats: Aggregated batch statistics
        file_stats: Per-file statistics
    """
    output = {
        "batch": batch_stats.to_dict(),
        "files": [stats.to_dict() for stats in file_stats],
    }
    print(json.dumps(output, indent=2))


# =============================================================================
# CLI Entry Point
# =============================================================================


def main() -> None:
    """CLI entry point for batch processing example."""
    parser = argparse.ArgumentParser(
        description="Process multiple OpenAI export files concurrently",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "files",
        nargs="+",
        type=Path,
        help="Paths to OpenAI export JSON files",
    )

    parser.add_argument(
        "--workers",
        "-w",
        type=int,
        default=None,
        help="Number of worker threads (default: CPU count)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose progress logging to stderr",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON to stdout (default: human-readable table to stderr)",
    )

    args = parser.parse_args()

    # Determine worker count (default to CPU count)
    import os

    workers = args.workers if args.workers is not None else os.cpu_count() or 4

    # Validate files
    for file_path in args.files:
        if not file_path.exists():
            print(
                f"Warning: File not found: {file_path} (will be marked as failed)",
                file=sys.stderr,
            )

    # Create batch processor
    processor = BatchProcessor(workers=workers, verbose=args.verbose)

    # Process files
    try:
        batch_stats, file_stats = processor.process_files(args.files)

        # Output results
        if args.json:
            # JSON to stdout (pipeline-friendly)
            print_json_output(batch_stats, file_stats)
        else:
            # Human-readable tables to stderr
            print_summary_table(batch_stats, file_stats)

        # Exit code based on success rate
        if batch_stats.files_failed > 0:
            sys.exit(1)  # Partial failure
        else:
            sys.exit(0)  # All successful

    except KeyboardInterrupt:
        print("\nBatch processing cancelled by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"\nBatch processing failed: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
