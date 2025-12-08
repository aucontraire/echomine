"""Test statistics models for conversation metadata.

This module tests the Pydantic models in echomine.models.statistics, including
ConversationSummary, RoleCount, ExportMetadata, ExportStatistics, and ConversationStatistics
validation and behavior.

Constitution Compliance:
    - Principle III: TDD (tests written FIRST before implementation)
    - Principle VI: Strict typing with mypy --strict compliance

Test Coverage:
    - T013: ConversationSummary validation (empty id fails, negative count fails)
    - T014: RoleCount.total property (sum of user + assistant + system)
    - T015: ExportMetadata immutability (frozen=True prevents modification)
    - T037: ExportStatistics model validates all required fields
    - T038: ConversationStatistics model validates all required fields
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from echomine.models.statistics import ConversationSummary, ExportMetadata, RoleCount


class TestConversationSummary:
    """Test ConversationSummary model validation and behavior."""

    def test_valid_conversation_summary(self) -> None:
        """Test ConversationSummary with valid fields."""
        summary = ConversationSummary(id="conv-001", title="Project Planning", message_count=42)

        assert summary.id == "conv-001"
        assert summary.title == "Project Planning"
        assert summary.message_count == 42

    def test_empty_id_fails(self) -> None:
        """Test ConversationSummary rejects empty id (T013)."""
        with pytest.raises(ValidationError) as exc_info:
            ConversationSummary(id="", title="Test", message_count=10)

        # Verify error message mentions min_length constraint
        error_str = str(exc_info.value)
        assert "id" in error_str.lower()

    def test_empty_title_fails(self) -> None:
        """Test ConversationSummary rejects empty title."""
        with pytest.raises(ValidationError) as exc_info:
            ConversationSummary(id="conv-001", title="", message_count=10)

        error_str = str(exc_info.value)
        assert "title" in error_str.lower()

    def test_negative_message_count_fails(self) -> None:
        """Test ConversationSummary rejects negative message_count (T013)."""
        with pytest.raises(ValidationError) as exc_info:
            ConversationSummary(id="conv-001", title="Test", message_count=-5)

        # Verify error message mentions validation constraint
        error_str = str(exc_info.value)
        assert "message_count" in error_str.lower()

    def test_zero_message_count_allowed(self) -> None:
        """Test ConversationSummary allows zero message_count (edge case)."""
        summary = ConversationSummary(id="conv-001", title="Empty", message_count=0)

        assert summary.message_count == 0

    def test_immutable_fields(self) -> None:
        """Test ConversationSummary fields are immutable (frozen=True)."""
        summary = ConversationSummary(id="conv-001", title="Test", message_count=10)

        # Attempt to modify id should raise ValidationError
        with pytest.raises(ValidationError):
            summary.id = "conv-002"  # pyright: ignore[reportAttributeAccessIssue]

        # Attempt to modify title should raise ValidationError
        with pytest.raises(ValidationError):
            summary.title = "New Title"  # pyright: ignore[reportAttributeAccessIssue]

        # Attempt to modify message_count should raise ValidationError
        with pytest.raises(ValidationError):
            summary.message_count = 20  # pyright: ignore[reportAttributeAccessIssue]

    def test_extra_fields_rejected(self) -> None:
        """Test ConversationSummary rejects unknown fields (extra='forbid')."""
        with pytest.raises(ValidationError) as exc_info:
            ConversationSummary(  # type: ignore[call-arg]
                id="conv-001",
                title="Test",
                message_count=10,
                extra_field="unexpected",
            )

        error_str = str(exc_info.value)
        assert "extra" in error_str.lower() or "unexpected" in error_str.lower()


class TestRoleCount:
    """Test RoleCount model validation and computed properties."""

    def test_valid_role_count(self) -> None:
        """Test RoleCount with valid fields."""
        role_count = RoleCount(user=10, assistant=8, system=2)

        assert role_count.user == 10
        assert role_count.assistant == 8
        assert role_count.system == 2

    def test_total_property(self) -> None:
        """Test RoleCount.total property computes sum correctly (T014)."""
        role_count = RoleCount(user=10, assistant=8, system=2)

        # Verify total is sum of all roles
        assert role_count.total == 20
        assert role_count.total == role_count.user + role_count.assistant + role_count.system

    def test_total_with_zeros(self) -> None:
        """Test RoleCount.total with some zero counts."""
        role_count = RoleCount(user=5, assistant=0, system=0)

        assert role_count.total == 5

    def test_total_all_zeros(self) -> None:
        """Test RoleCount.total with all zero counts (default values)."""
        role_count = RoleCount()

        assert role_count.user == 0
        assert role_count.assistant == 0
        assert role_count.system == 0
        assert role_count.total == 0

    def test_default_values(self) -> None:
        """Test RoleCount uses default=0 for all fields."""
        role_count = RoleCount()

        assert role_count.user == 0
        assert role_count.assistant == 0
        assert role_count.system == 0

    def test_partial_defaults(self) -> None:
        """Test RoleCount allows partial field specification."""
        role_count = RoleCount(user=5)

        assert role_count.user == 5
        assert role_count.assistant == 0
        assert role_count.system == 0
        assert role_count.total == 5

    def test_negative_counts_rejected(self) -> None:
        """Test RoleCount rejects negative counts (ge=0 constraint)."""
        # Negative user count
        with pytest.raises(ValidationError) as exc_info:
            RoleCount(user=-1, assistant=0, system=0)
        assert "user" in str(exc_info.value).lower()

        # Negative assistant count
        with pytest.raises(ValidationError) as exc_info:
            RoleCount(user=0, assistant=-5, system=0)
        assert "assistant" in str(exc_info.value).lower()

        # Negative system count
        with pytest.raises(ValidationError) as exc_info:
            RoleCount(user=0, assistant=0, system=-2)
        assert "system" in str(exc_info.value).lower()

    def test_immutable_fields(self) -> None:
        """Test RoleCount fields are immutable (frozen=True)."""
        role_count = RoleCount(user=10, assistant=8, system=2)

        # Attempt to modify user should raise ValidationError
        with pytest.raises(ValidationError):
            role_count.user = 20  # pyright: ignore[reportAttributeAccessIssue]

        # Attempt to modify assistant should raise ValidationError
        with pytest.raises(ValidationError):
            role_count.assistant = 15  # pyright: ignore[reportAttributeAccessIssue]

        # Attempt to modify system should raise ValidationError
        with pytest.raises(ValidationError):
            role_count.system = 5  # pyright: ignore[reportAttributeAccessIssue]

    def test_extra_fields_rejected(self) -> None:
        """Test RoleCount rejects unknown fields (extra='forbid')."""
        with pytest.raises(ValidationError) as exc_info:
            RoleCount(  # type: ignore[call-arg]
                user=10, assistant=8, system=2, other=5
            )

        error_str = str(exc_info.value).lower()
        assert "extra" in error_str or "other" in error_str


class TestExportMetadata:
    """Test ExportMetadata model validation and immutability."""

    def test_valid_export_metadata(self) -> None:
        """Test ExportMetadata with valid fields."""
        created = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        updated = datetime(2024, 1, 15, 18, 30, 0, tzinfo=UTC)
        exported = datetime(2024, 2, 1, 10, 0, 0, tzinfo=UTC)

        metadata = ExportMetadata(
            id="conv-001",
            title="Project Planning",
            created_at=created,
            updated_at=updated,
            message_count=42,
            export_date=exported,
            exported_by="echomine",
        )

        assert metadata.id == "conv-001"
        assert metadata.title == "Project Planning"
        assert metadata.created_at == created
        assert metadata.updated_at == updated
        assert metadata.message_count == 42
        assert metadata.export_date == exported
        assert metadata.exported_by == "echomine"

    def test_optional_updated_at(self) -> None:
        """Test ExportMetadata allows None for updated_at."""
        created = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        exported = datetime(2024, 2, 1, 10, 0, 0, tzinfo=UTC)

        metadata = ExportMetadata(
            id="conv-002",
            title="Test",
            created_at=created,
            updated_at=None,
            message_count=5,
            export_date=exported,
        )

        assert metadata.updated_at is None

    def test_default_exported_by(self) -> None:
        """Test ExportMetadata uses default='echomine' for exported_by."""
        created = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        exported = datetime(2024, 2, 1, 10, 0, 0, tzinfo=UTC)

        metadata = ExportMetadata(
            id="conv-003",
            title="Test",
            created_at=created,
            message_count=5,
            export_date=exported,
        )

        assert metadata.exported_by == "echomine"

    def test_immutable_fields(self) -> None:
        """Test ExportMetadata fields are immutable (T015)."""
        created = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        exported = datetime(2024, 2, 1, 10, 0, 0, tzinfo=UTC)

        metadata = ExportMetadata(
            id="conv-001",
            title="Test",
            created_at=created,
            message_count=10,
            export_date=exported,
        )

        # Attempt to modify id should raise ValidationError (frozen=True)
        with pytest.raises(ValidationError):
            metadata.id = "conv-002"  # pyright: ignore[reportAttributeAccessIssue]

        # Attempt to modify title should raise ValidationError
        with pytest.raises(ValidationError):
            metadata.title = "New Title"  # pyright: ignore[reportAttributeAccessIssue]

        # Attempt to modify message_count should raise ValidationError
        with pytest.raises(ValidationError):
            metadata.message_count = 20  # pyright: ignore[reportAttributeAccessIssue]

    def test_negative_message_count_rejected(self) -> None:
        """Test ExportMetadata rejects negative message_count."""
        created = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        exported = datetime(2024, 2, 1, 10, 0, 0, tzinfo=UTC)

        with pytest.raises(ValidationError) as exc_info:
            ExportMetadata(
                id="conv-001",
                title="Test",
                created_at=created,
                message_count=-5,
                export_date=exported,
            )

        error_str = str(exc_info.value).lower()
        assert "message_count" in error_str

    def test_extra_fields_rejected(self) -> None:
        """Test ExportMetadata rejects unknown fields (extra='forbid')."""
        created = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        exported = datetime(2024, 2, 1, 10, 0, 0, tzinfo=UTC)

        with pytest.raises(ValidationError) as exc_info:
            ExportMetadata(  # type: ignore[call-arg]
                id="conv-001",
                title="Test",
                created_at=created,
                message_count=10,
                export_date=exported,
                extra_field="unexpected",
            )

        error_str = str(exc_info.value).lower()
        assert "extra" in error_str or "unexpected" in error_str


class TestExportStatistics:
    """Test ExportStatistics model validation and behavior (T037)."""

    def test_valid_export_statistics(self) -> None:
        """Test ExportStatistics with all required fields."""
        from echomine.models.statistics import ExportStatistics

        earliest = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        latest = datetime(2024, 12, 5, 18, 30, 0, tzinfo=UTC)

        largest = ConversationSummary(id="conv-large", title="Deep Discussion", message_count=245)
        smallest = ConversationSummary(id="conv-small", title="Quick Q", message_count=2)

        stats = ExportStatistics(
            total_conversations=1234,
            total_messages=45678,
            earliest_date=earliest,
            latest_date=latest,
            average_messages=37.0,
            largest_conversation=largest,
            smallest_conversation=smallest,
            skipped_count=3,
        )

        assert stats.total_conversations == 1234
        assert stats.total_messages == 45678
        assert stats.earliest_date == earliest
        assert stats.latest_date == latest
        assert stats.average_messages == 37.0
        assert stats.largest_conversation == largest
        assert stats.smallest_conversation == smallest
        assert stats.skipped_count == 3

    def test_optional_fields_none(self) -> None:
        """Test ExportStatistics allows None for optional fields (empty export)."""
        from echomine.models.statistics import ExportStatistics

        stats = ExportStatistics(
            total_conversations=0,
            total_messages=0,
            earliest_date=None,
            latest_date=None,
            average_messages=0.0,
            largest_conversation=None,
            smallest_conversation=None,
            skipped_count=0,
        )

        assert stats.total_conversations == 0
        assert stats.total_messages == 0
        assert stats.earliest_date is None
        assert stats.latest_date is None
        assert stats.average_messages == 0.0
        assert stats.largest_conversation is None
        assert stats.smallest_conversation is None
        assert stats.skipped_count == 0

    def test_negative_total_conversations_rejected(self) -> None:
        """Test ExportStatistics rejects negative total_conversations."""
        from echomine.models.statistics import ExportStatistics

        with pytest.raises(ValidationError) as exc_info:
            ExportStatistics(
                total_conversations=-1,
                total_messages=100,
                average_messages=10.0,
            )

        error_str = str(exc_info.value).lower()
        assert "total_conversations" in error_str

    def test_negative_total_messages_rejected(self) -> None:
        """Test ExportStatistics rejects negative total_messages."""
        from echomine.models.statistics import ExportStatistics

        with pytest.raises(ValidationError) as exc_info:
            ExportStatistics(
                total_conversations=10,
                total_messages=-100,
                average_messages=10.0,
            )

        error_str = str(exc_info.value).lower()
        assert "total_messages" in error_str

    def test_negative_average_messages_rejected(self) -> None:
        """Test ExportStatistics rejects negative average_messages."""
        from echomine.models.statistics import ExportStatistics

        with pytest.raises(ValidationError) as exc_info:
            ExportStatistics(
                total_conversations=10,
                total_messages=100,
                average_messages=-5.0,
            )

        error_str = str(exc_info.value).lower()
        assert "average_messages" in error_str

    def test_negative_skipped_count_rejected(self) -> None:
        """Test ExportStatistics rejects negative skipped_count."""
        from echomine.models.statistics import ExportStatistics

        with pytest.raises(ValidationError) as exc_info:
            ExportStatistics(
                total_conversations=10,
                total_messages=100,
                average_messages=10.0,
                skipped_count=-5,
            )

        error_str = str(exc_info.value).lower()
        assert "skipped_count" in error_str

    def test_immutable_fields(self) -> None:
        """Test ExportStatistics fields are immutable (frozen=True)."""
        from echomine.models.statistics import ExportStatistics

        stats = ExportStatistics(
            total_conversations=10,
            total_messages=100,
            average_messages=10.0,
        )

        # Attempt to modify total_conversations should raise ValidationError
        with pytest.raises(ValidationError):
            stats.total_conversations = 20  # pyright: ignore[reportAttributeAccessIssue]

    def test_extra_fields_rejected(self) -> None:
        """Test ExportStatistics rejects unknown fields (extra='forbid')."""
        from echomine.models.statistics import ExportStatistics

        with pytest.raises(ValidationError) as exc_info:
            ExportStatistics(  # type: ignore[call-arg]
                total_conversations=10,
                total_messages=100,
                average_messages=10.0,
                extra_field="unexpected",
            )

        error_str = str(exc_info.value).lower()
        assert "extra" in error_str or "unexpected" in error_str


class TestConversationStatistics:
    """Test ConversationStatistics model validation and behavior (T038)."""

    def test_valid_conversation_statistics(self) -> None:
        """Test ConversationStatistics with all required fields."""
        from echomine.models.statistics import ConversationStatistics

        created = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)
        updated = datetime(2024, 1, 15, 14, 45, 0, tzinfo=UTC)
        first_msg = datetime(2024, 1, 15, 10, 30, 5, tzinfo=UTC)
        last_msg = datetime(2024, 1, 15, 14, 44, 32, tzinfo=UTC)

        role_count = RoleCount(user=82, assistant=155, system=8)

        stats = ConversationStatistics(
            conversation_id="conv-123",
            title="Deep Python Discussion",
            created_at=created,
            updated_at=updated,
            message_count=245,
            message_count_by_role=role_count,
            first_message=first_msg,
            last_message=last_msg,
            duration_seconds=15267.0,
            average_gap_seconds=62.3,
        )

        assert stats.conversation_id == "conv-123"
        assert stats.title == "Deep Python Discussion"
        assert stats.created_at == created
        assert stats.updated_at == updated
        assert stats.message_count == 245
        assert stats.message_count_by_role == role_count
        assert stats.first_message == first_msg
        assert stats.last_message == last_msg
        assert stats.duration_seconds == 15267.0
        assert stats.average_gap_seconds == 62.3

    def test_optional_updated_at_none(self) -> None:
        """Test ConversationStatistics allows None for updated_at."""
        from echomine.models.statistics import ConversationStatistics

        created = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)

        stats = ConversationStatistics(
            conversation_id="conv-123",
            title="Test",
            created_at=created,
            updated_at=None,
            message_count=5,
            message_count_by_role=RoleCount(user=5),
        )

        assert stats.updated_at is None

    def test_optional_first_last_message_none(self) -> None:
        """Test ConversationStatistics allows None for first_message and last_message (no messages)."""
        from echomine.models.statistics import ConversationStatistics

        created = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)

        stats = ConversationStatistics(
            conversation_id="conv-123",
            title="Empty Conversation",
            created_at=created,
            message_count=0,
            message_count_by_role=RoleCount(),
            first_message=None,
            last_message=None,
            duration_seconds=0.0,
            average_gap_seconds=None,
        )

        assert stats.first_message is None
        assert stats.last_message is None
        assert stats.duration_seconds == 0.0
        assert stats.average_gap_seconds is None

    def test_average_gap_none_for_single_message(self) -> None:
        """Test ConversationStatistics allows None for average_gap_seconds (<2 messages)."""
        from echomine.models.statistics import ConversationStatistics

        created = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)
        first_msg = datetime(2024, 1, 15, 10, 30, 5, tzinfo=UTC)

        stats = ConversationStatistics(
            conversation_id="conv-123",
            title="Single Message",
            created_at=created,
            message_count=1,
            message_count_by_role=RoleCount(user=1),
            first_message=first_msg,
            last_message=first_msg,
            duration_seconds=0.0,
            average_gap_seconds=None,
        )

        assert stats.average_gap_seconds is None

    def test_empty_conversation_id_rejected(self) -> None:
        """Test ConversationStatistics rejects empty conversation_id."""
        from echomine.models.statistics import ConversationStatistics

        created = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)

        with pytest.raises(ValidationError) as exc_info:
            ConversationStatistics(
                conversation_id="",
                title="Test",
                created_at=created,
                message_count=5,
                message_count_by_role=RoleCount(user=5),
            )

        error_str = str(exc_info.value).lower()
        assert "conversation_id" in error_str

    def test_empty_title_rejected(self) -> None:
        """Test ConversationStatistics rejects empty title."""
        from echomine.models.statistics import ConversationStatistics

        created = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)

        with pytest.raises(ValidationError) as exc_info:
            ConversationStatistics(
                conversation_id="conv-123",
                title="",
                created_at=created,
                message_count=5,
                message_count_by_role=RoleCount(user=5),
            )

        error_str = str(exc_info.value).lower()
        assert "title" in error_str

    def test_negative_message_count_rejected(self) -> None:
        """Test ConversationStatistics rejects negative message_count."""
        from echomine.models.statistics import ConversationStatistics

        created = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)

        with pytest.raises(ValidationError) as exc_info:
            ConversationStatistics(
                conversation_id="conv-123",
                title="Test",
                created_at=created,
                message_count=-5,
                message_count_by_role=RoleCount(),
            )

        error_str = str(exc_info.value).lower()
        assert "message_count" in error_str

    def test_negative_duration_rejected(self) -> None:
        """Test ConversationStatistics rejects negative duration_seconds."""
        from echomine.models.statistics import ConversationStatistics

        created = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)

        with pytest.raises(ValidationError) as exc_info:
            ConversationStatistics(
                conversation_id="conv-123",
                title="Test",
                created_at=created,
                message_count=5,
                message_count_by_role=RoleCount(user=5),
                duration_seconds=-100.0,
            )

        error_str = str(exc_info.value).lower()
        assert "duration_seconds" in error_str

    def test_immutable_fields(self) -> None:
        """Test ConversationStatistics fields are immutable (frozen=True)."""
        from echomine.models.statistics import ConversationStatistics

        created = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)

        stats = ConversationStatistics(
            conversation_id="conv-123",
            title="Test",
            created_at=created,
            message_count=5,
            message_count_by_role=RoleCount(user=5),
        )

        # Attempt to modify conversation_id should raise ValidationError
        with pytest.raises(ValidationError):
            stats.conversation_id = "conv-456"  # pyright: ignore[reportAttributeAccessIssue]

    def test_extra_fields_rejected(self) -> None:
        """Test ConversationStatistics rejects unknown fields (extra='forbid')."""
        from echomine.models.statistics import ConversationStatistics

        created = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)

        with pytest.raises(ValidationError) as exc_info:
            ConversationStatistics(  # type: ignore[call-arg]
                conversation_id="conv-123",
                title="Test",
                created_at=created,
                message_count=5,
                message_count_by_role=RoleCount(user=5),
                extra_field="unexpected",
            )

        error_str = str(exc_info.value).lower()
        assert "extra" in error_str or "unexpected" in error_str
