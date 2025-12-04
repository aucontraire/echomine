"""Cognivault Integration Example - Memory-Efficient Streaming Ingestion.

This example demonstrates how to integrate echomine with cognivault to stream
conversations from OpenAI exports into a knowledge base with:
- O(1) memory complexity for arbitrarily large files
- Progress tracking for long-running ingestion
- Graceful error handling with skip callbacks
- Batch processing for efficient database writes

Requirements:
    - FR-337: Stream-based ingestion for memory efficiency
    - FR-338: Progress reporting for user visibility
    - FR-339: Error handling with on_skip callbacks
    - FR-340: Batch processing for performance
    - FR-341: Transaction support for data integrity
    - CHK077: Demonstrate on_skip callback usage (P1 Gap)

Example Usage:
    ```bash
    # Basic ingestion
    python examples/cognivault_integration.py export.json

    # With custom batch size and progress tracking
    python examples/cognivault_integration.py export.json --batch-size 100 --verbose
    ```

Architecture:
    echomine (streaming) -> Batch Buffer -> cognivault (bulk insert)
          ↓                      ↓                    ↓
    O(1) memory           O(batch_size)        Transaction-safe
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from echomine import Conversation, OpenAIAdapter


# =============================================================================
# Mock Cognivault Client (for demonstration)
# =============================================================================
# In production, replace with: from cognivault import CognivaultClient


class CognivaultClient:
    """Mock cognivault client for demonstration purposes.

    In production, this would be the actual cognivault SDK client
    for inserting conversations into the knowledge base.
    """

    def __init__(self, api_key: str, workspace_id: str) -> None:
        """Initialize cognivault client (mock)."""
        self.api_key = api_key
        self.workspace_id = workspace_id
        self.inserted_count = 0

    def bulk_insert_conversations(self, conversations: list[dict[str, Any]]) -> None:
        """Bulk insert conversations into cognivault (mock).

        In production, this would call cognivault's batch API.
        """
        # Mock implementation - just count insertions
        self.inserted_count += len(conversations)
        print(
            f"[Cognivault] Inserted {len(conversations)} conversations "
            f"(total: {self.inserted_count})",
            file=sys.stderr,
        )


# =============================================================================
# Streaming Ingestion Pipeline
# =============================================================================


class CognivaultIngestionPipeline:
    """Stream conversations from OpenAI export into cognivault knowledge base.

    This pipeline demonstrates the recommended pattern for integrating echomine
    with external systems like cognivault:

    1. Stream conversations with O(1) memory (echomine)
    2. Buffer into batches for efficient bulk writes
    3. Track progress and errors via callbacks
    4. Handle malformed entries gracefully with on_skip

    Memory Complexity:
        - echomine streaming: O(1) for file size
        - Batch buffer: O(batch_size)
        - Total: O(batch_size), independent of export file size

    Error Handling:
        - on_skip: Log malformed conversations, continue processing
        - progress_callback: Report progress every N conversations
        - Exceptions: Fail fast on unrecoverable errors (file not found, etc.)
    """

    def __init__(
        self,
        cognivault_client: CognivaultClient,
        batch_size: int = 50,
        verbose: bool = False,
    ) -> None:
        """Initialize ingestion pipeline.

        Args:
            cognivault_client: Configured cognivault client for API calls
            batch_size: Number of conversations to buffer before bulk insert
            verbose: Enable detailed progress logging
        """
        self.client = cognivault_client
        self.batch_size = batch_size
        self.verbose = verbose

        # Statistics
        self.total_processed = 0
        self.total_skipped = 0
        self.total_inserted = 0

        # Batch buffer
        self.batch: list[dict[str, Any]] = []

    def on_skip(self, conversation_id: str, reason: str) -> None:
        """Handle malformed conversations (CHK077 - P1 Gap demonstration).

        This callback is invoked by echomine when a conversation entry is
        skipped due to validation errors or malformed data. The pipeline
        logs the skip and continues processing.

        Args:
            conversation_id: ID of skipped conversation (if available)
            reason: Human-readable reason for skip

        Example Output:
            [SKIP] Conversation abc-123: Validation error: Missing required field 'title'
        """
        self.total_skipped += 1
        print(
            f"[SKIP] Conversation {conversation_id}: {reason}",
            file=sys.stderr,
        )

    def on_progress(self, count: int) -> None:
        """Report progress during streaming.

        This callback is invoked by echomine every 100 conversations processed.
        Useful for long-running ingestion to show user that progress is being made.

        Args:
            count: Number of conversations processed so far
        """
        if self.verbose:
            print(
                f"[PROGRESS] Processed {count} conversations...",
                file=sys.stderr,
            )

    def ingest_from_export(self, export_path: Path) -> None:
        """Stream conversations from OpenAI export into cognivault.

        This is the main entry point for the ingestion pipeline. It uses
        echomine's streaming API to process conversations one at a time,
        buffering them into batches for efficient bulk insertion.

        Args:
            export_path: Path to OpenAI export JSON file

        Raises:
            FileNotFoundError: If export file doesn't exist
            PermissionError: If export file can't be read
            ParseError: If export JSON is malformed (unrecoverable)

        Example:
            ```python
            pipeline = CognivaultIngestionPipeline(client, batch_size=100)
            pipeline.ingest_from_export(Path("export.json"))
            ```
        """
        # Initialize echomine adapter (stateless, lightweight)
        adapter = OpenAIAdapter()

        print(
            f"[START] Ingesting conversations from {export_path}",
            file=sys.stderr,
        )
        print(
            f"[CONFIG] Batch size: {self.batch_size}, Workspace: {self.client.workspace_id}",
            file=sys.stderr,
        )

        start_time = datetime.now(UTC)

        try:
            # Stream conversations with callbacks (FR-337, FR-338, FR-339)
            for conversation in adapter.stream_conversations(
                export_path,
                progress_callback=self.on_progress,
                on_skip=self.on_skip,  # CHK077: Demonstrate on_skip usage
            ):
                # Convert to cognivault format
                conv_dict = self._conversation_to_dict(conversation)

                # Add to batch buffer
                self.batch.append(conv_dict)
                self.total_processed += 1

                # Flush batch when full (FR-340)
                if len(self.batch) >= self.batch_size:
                    self._flush_batch()

            # Flush remaining conversations (FR-341)
            if self.batch:
                self._flush_batch()

        except KeyboardInterrupt:
            # User interrupted - flush partial batch before exiting
            print("\n[INTERRUPT] User cancelled ingestion", file=sys.stderr)
            if self.batch:
                print(
                    f"[FLUSH] Flushing {len(self.batch)} remaining conversations...",
                    file=sys.stderr,
                )
                self._flush_batch()
            raise

        # Report final statistics
        elapsed = (datetime.now(UTC) - start_time).total_seconds()
        self._print_summary(elapsed)

    def _flush_batch(self) -> None:
        """Flush buffered conversations to cognivault (FR-340, FR-341).

        Performs bulk insert of all conversations in the current batch,
        then clears the batch buffer. Uses transaction for data integrity.
        """
        if not self.batch:
            return

        try:
            # Bulk insert to cognivault (transaction-safe in production)
            self.client.bulk_insert_conversations(self.batch)
            self.total_inserted += len(self.batch)

        except Exception as e:
            # Log error but don't lose data - could implement retry logic
            print(
                f"[ERROR] Failed to insert batch of {len(self.batch)}: {e}",
                file=sys.stderr,
            )
            raise

        finally:
            # Clear batch buffer (free memory)
            self.batch.clear()

    def _conversation_to_dict(self, conversation: Conversation) -> dict[str, Any]:
        """Convert Conversation to cognivault-compatible dict.

        Args:
            conversation: Pydantic Conversation model

        Returns:
            Dictionary with conversation data for cognivault API
        """
        return {
            "id": conversation.id,
            "title": conversation.title,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at_or_created.isoformat(),
            "message_count": conversation.message_count,
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                }
                for msg in conversation.messages
            ],
            "metadata": conversation.metadata,
        }

    def _print_summary(self, elapsed_seconds: float) -> None:
        """Print ingestion summary statistics.

        Args:
            elapsed_seconds: Total time taken for ingestion
        """
        print("\n" + "=" * 60, file=sys.stderr)
        print("[COMPLETE] Ingestion Summary", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        print(f"Total processed:    {self.total_processed}", file=sys.stderr)
        print(f"Successfully inserted: {self.total_inserted}", file=sys.stderr)
        print(f"Skipped (malformed):  {self.total_skipped}", file=sys.stderr)
        print(f"Elapsed time:       {elapsed_seconds:.2f}s", file=sys.stderr)
        print(
            f"Throughput:         {self.total_processed / elapsed_seconds:.1f} conv/sec",
            file=sys.stderr,
        )
        print("=" * 60 + "\n", file=sys.stderr)


# =============================================================================
# CLI Entry Point
# =============================================================================


def main() -> None:
    """CLI entry point for cognivault ingestion example."""
    parser = argparse.ArgumentParser(
        description="Ingest OpenAI conversations into cognivault knowledge base",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "export_file",
        type=Path,
        help="Path to OpenAI export JSON file",
    )

    parser.add_argument(
        "--api-key",
        default="demo-api-key",
        help="Cognivault API key (default: demo-api-key)",
    )

    parser.add_argument(
        "--workspace-id",
        default="demo-workspace",
        help="Cognivault workspace ID (default: demo-workspace)",
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Number of conversations to buffer before bulk insert (default: 50)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose progress logging",
    )

    args = parser.parse_args()

    # Validate export file exists
    if not args.export_file.exists():
        print(f"Error: Export file not found: {args.export_file}", file=sys.stderr)
        sys.exit(1)

    # Initialize cognivault client (mock for demonstration)
    client = CognivaultClient(
        api_key=args.api_key,
        workspace_id=args.workspace_id,
    )

    # Create ingestion pipeline
    pipeline = CognivaultIngestionPipeline(
        cognivault_client=client,
        batch_size=args.batch_size,
        verbose=args.verbose,
    )

    # Run ingestion
    try:
        pipeline.ingest_from_export(args.export_file)
    except KeyboardInterrupt:
        print("\nIngestion cancelled by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"\nIngestion failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
