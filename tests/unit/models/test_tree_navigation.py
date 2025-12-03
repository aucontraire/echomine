"""Tree Navigation Contract Tests for Conversation Model.

This test module validates the tree navigation methods in the Conversation model
(get_root_messages, get_children, get_thread, get_all_threads) to ensure correct
parent-child relationship traversal and thread extraction.

Test Strategy:
    - Test get_root_messages() with single/multiple/zero roots
    - Test get_children() with no/single/multiple children
    - Test get_thread() with root/leaf/mid-level/non-existent messages
    - Test get_all_threads() with linear/branching/complex tree structures
    - Use pytest fixtures for reusable conversation structures
    - Validate behavior, not implementation (check lengths, IDs, order)

Constitution Compliance:
    - Principle VI: Strict Typing Mandatory (mypy --strict compliance)
    - Principle III: Test-Driven Development (RED-GREEN-REFACTOR)
    - FR-278: Support tree navigation via parent-child relationships
    - FR-280: Enable analysis of all conversation branches

Requirements Coverage:
    - FR-278: Tree navigation support (get_children, get_thread, get_root_messages)
    - FR-280: Comprehensive tree traversal (get_all_threads)

Test Execution:
    pytest tests/unit/models/test_tree_navigation.py -v --cov=echomine.models.conversation

Expected Coverage Improvement:
    - Before: ~48% (lines 262-388 mostly untested)
    - After: ~80%+ (all 4 methods with multiple scenarios)
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from echomine import Conversation, Message


# ============================================================================
# Test Fixtures: Reusable Conversation Structures
# ============================================================================


# NOTE: empty_conversation fixture is NOT included because Conversation model
# enforces min_length=1 validation on messages (line 108 in conversation.py).
# This is correct by design - conversations without messages are invalid.
# Tree navigation methods don't need to handle empty conversations.


@pytest.fixture
def single_message_conversation() -> Conversation:
    """Linear conversation with single message (root only).

    Structure:
        msg-1 (user: "Hello") [ROOT, LEAF]

    Returns:
        Conversation with 1 message
    """
    msg = Message(
        id="msg-1",
        content="Hello",
        role="user",
        timestamp=datetime.now(UTC),
        parent_id=None,
    )

    return Conversation(
        id="conv-single",
        title="Single Message",
        created_at=datetime.now(UTC),
        updated_at=None,
        messages=[msg],
    )


@pytest.fixture
def linear_conversation() -> Conversation:
    """Linear conversation with 3 messages (no branching).

    Structure:
        msg-1 (user: "Hello")               [ROOT]
        └── msg-2 (assistant: "Hi!")        [CHILD of msg-1]
            └── msg-3 (user: "How are you?") [CHILD of msg-2, LEAF]

    Returns:
        Conversation with 3 messages in linear chain
    """
    base_time = datetime.now(UTC)

    messages = [
        Message(
            id="msg-1",
            content="Hello",
            role="user",
            timestamp=base_time,
            parent_id=None,
        ),
        Message(
            id="msg-2",
            content="Hi!",
            role="assistant",
            timestamp=base_time + timedelta(seconds=1),
            parent_id="msg-1",
        ),
        Message(
            id="msg-3",
            content="How are you?",
            role="user",
            timestamp=base_time + timedelta(seconds=2),
            parent_id="msg-2",
        ),
    ]

    return Conversation(
        id="conv-linear",
        title="Linear Conversation",
        created_at=base_time,
        updated_at=None,
        messages=messages,
    )


@pytest.fixture
def branching_conversation() -> Conversation:
    """Branching conversation with multiple paths.

    Structure:
        msg-1 (user: "Hello")                    [ROOT]
        ├── msg-2 (assistant: "Hi!")             [CHILD of msg-1]
        │   └── msg-4 (user: "How are you?")     [CHILD of msg-2, LEAF]
        └── msg-3 (assistant: "Alternative")     [CHILD of msg-1, LEAF]

    Expected Threads:
        Thread 1: [msg-1, msg-2, msg-4]
        Thread 2: [msg-1, msg-3]

    Returns:
        Conversation with 4 messages and 2 branches
    """
    base_time = datetime.now(UTC)

    messages = [
        Message(
            id="msg-1",
            content="Hello",
            role="user",
            timestamp=base_time,
            parent_id=None,
        ),
        Message(
            id="msg-2",
            content="Hi!",
            role="assistant",
            timestamp=base_time + timedelta(seconds=1),
            parent_id="msg-1",
        ),
        Message(
            id="msg-3",
            content="Alternative",
            role="assistant",
            timestamp=base_time + timedelta(seconds=2),
            parent_id="msg-1",
        ),
        Message(
            id="msg-4",
            content="How are you?",
            role="user",
            timestamp=base_time + timedelta(seconds=3),
            parent_id="msg-2",
        ),
    ]

    return Conversation(
        id="conv-branching",
        title="Branching Conversation",
        created_at=base_time,
        updated_at=None,
        messages=messages,
    )


@pytest.fixture
def multi_root_conversation() -> Conversation:
    """Conversation with multiple root messages (unusual but valid).

    Structure:
        msg-1 (user: "Hello")                [ROOT]
        └── msg-2 (assistant: "Hi!")         [CHILD of msg-1, LEAF]
        msg-3 (system: "Session started")    [ROOT, LEAF]

    Expected Threads:
        Thread 1: [msg-1, msg-2]
        Thread 2: [msg-3]

    Returns:
        Conversation with 2 root messages
    """
    base_time = datetime.now(UTC)

    messages = [
        Message(
            id="msg-1",
            content="Hello",
            role="user",
            timestamp=base_time,
            parent_id=None,
        ),
        Message(
            id="msg-2",
            content="Hi!",
            role="assistant",
            timestamp=base_time + timedelta(seconds=1),
            parent_id="msg-1",
        ),
        Message(
            id="msg-3",
            content="Session started",
            role="system",
            timestamp=base_time + timedelta(seconds=2),
            parent_id=None,
        ),
    ]

    return Conversation(
        id="conv-multi-root",
        title="Multi-Root Conversation",
        created_at=base_time,
        updated_at=None,
        messages=messages,
    )


@pytest.fixture
def complex_tree_conversation() -> Conversation:
    """Complex conversation tree with multiple branches and depths.

    Structure:
        msg-1 (user: "Hello")                     [ROOT]
        ├── msg-2 (assistant: "Hi!")              [CHILD of msg-1]
        │   ├── msg-4 (user: "Question 1")        [CHILD of msg-2]
        │   │   └── msg-6 (assistant: "Answer 1") [CHILD of msg-4, LEAF]
        │   └── msg-5 (user: "Question 2")        [CHILD of msg-2, LEAF]
        └── msg-3 (assistant: "Alternative")      [CHILD of msg-1, LEAF]

    Expected Threads:
        Thread 1: [msg-1, msg-2, msg-4, msg-6]
        Thread 2: [msg-1, msg-2, msg-5]
        Thread 3: [msg-1, msg-3]

    Returns:
        Conversation with 6 messages and 3 distinct paths
    """
    base_time = datetime.now(UTC)

    messages = [
        Message(
            id="msg-1",
            content="Hello",
            role="user",
            timestamp=base_time,
            parent_id=None,
        ),
        Message(
            id="msg-2",
            content="Hi!",
            role="assistant",
            timestamp=base_time + timedelta(seconds=1),
            parent_id="msg-1",
        ),
        Message(
            id="msg-3",
            content="Alternative",
            role="assistant",
            timestamp=base_time + timedelta(seconds=2),
            parent_id="msg-1",
        ),
        Message(
            id="msg-4",
            content="Question 1",
            role="user",
            timestamp=base_time + timedelta(seconds=3),
            parent_id="msg-2",
        ),
        Message(
            id="msg-5",
            content="Question 2",
            role="user",
            timestamp=base_time + timedelta(seconds=4),
            parent_id="msg-2",
        ),
        Message(
            id="msg-6",
            content="Answer 1",
            role="assistant",
            timestamp=base_time + timedelta(seconds=5),
            parent_id="msg-4",
        ),
    ]

    return Conversation(
        id="conv-complex",
        title="Complex Tree Conversation",
        created_at=base_time,
        updated_at=None,
        messages=messages,
    )


# ============================================================================
# T070-001: get_root_messages() Tests
# ============================================================================


def test_get_root_messages_with_single_root(
    linear_conversation: Conversation,
) -> None:
    """Verify get_root_messages() returns single root in linear conversation.

    Requirements:
        - FR-278: Support identifying conversation entry points
        - Linear conversation has exactly one root message

    Args:
        linear_conversation: Fixture with 3 messages in linear chain
    """
    roots = linear_conversation.get_root_messages()

    assert len(roots) == 1, "Linear conversation should have exactly 1 root"
    assert roots[0].id == "msg-1", "First message should be the root"
    assert roots[0].parent_id is None, "Root message must have parent_id=None"
    assert roots[0].content == "Hello", "Root message content should match fixture"


def test_get_root_messages_with_multiple_roots(
    multi_root_conversation: Conversation,
) -> None:
    """Verify get_root_messages() returns all root messages.

    Requirements:
        - FR-278: Support identifying conversation entry points
        - Multiple root messages should all be returned

    Args:
        multi_root_conversation: Fixture with 2 root messages
    """
    roots = multi_root_conversation.get_root_messages()

    assert len(roots) == 2, "Multi-root conversation should have 2 roots"

    root_ids = {msg.id for msg in roots}
    assert root_ids == {"msg-1", "msg-3"}, "Both root messages should be returned"

    # Verify all returned messages have parent_id=None
    for root in roots:
        assert root.parent_id is None, f"Root message {root.id} must have parent_id=None"


# ============================================================================
# T070-002: get_children() Tests
# ============================================================================


def test_get_children_with_no_children(linear_conversation: Conversation) -> None:
    """Verify get_children() returns empty list for leaf message.

    Requirements:
        - FR-278: Support tree navigation via parent-child relationships
        - Leaf messages have no children

    Args:
        linear_conversation: Fixture with 3 messages (msg-3 is leaf)
    """
    children = linear_conversation.get_children("msg-3")

    assert isinstance(children, list), "get_children() must return list"
    assert len(children) == 0, "Leaf message should have no children"


def test_get_children_with_single_child(linear_conversation: Conversation) -> None:
    """Verify get_children() returns single child in linear path.

    Requirements:
        - FR-278: Support tree navigation via parent-child relationships
        - Single-child message should return list with 1 element

    Args:
        linear_conversation: Fixture with 3 messages (msg-1 -> msg-2 -> msg-3)
    """
    children = linear_conversation.get_children("msg-1")

    assert len(children) == 1, "msg-1 should have exactly 1 child"
    assert children[0].id == "msg-2", "Child should be msg-2"
    assert children[0].parent_id == "msg-1", "Child's parent_id must reference parent"


def test_get_children_with_multiple_children(
    branching_conversation: Conversation,
) -> None:
    """Verify get_children() returns all direct children at branch point.

    Requirements:
        - FR-278: Support tree navigation via parent-child relationships
        - Branch messages should return all direct children

    Args:
        branching_conversation: Fixture with msg-1 having 2 children (msg-2, msg-3)
    """
    children = branching_conversation.get_children("msg-1")

    assert len(children) == 2, "msg-1 should have exactly 2 children"

    child_ids = {msg.id for msg in children}
    assert child_ids == {"msg-2", "msg-3"}, "Both children should be returned"

    # Verify all children reference the correct parent
    for child in children:
        assert child.parent_id == "msg-1", f"Child {child.id} must reference msg-1"


def test_get_children_with_non_existent_message_id(
    linear_conversation: Conversation,
) -> None:
    """Verify get_children() returns empty list for non-existent message ID.

    Requirements:
        - FR-278: Support tree navigation via parent-child relationships
        - Graceful handling of invalid message IDs

    Args:
        linear_conversation: Fixture with 3 messages
    """
    children = linear_conversation.get_children("msg-non-existent")

    assert isinstance(children, list), "get_children() must return list"
    assert len(children) == 0, "Non-existent message should have no children"


# ============================================================================
# T070-003: get_thread() Tests
# ============================================================================


def test_get_thread_for_root_message(linear_conversation: Conversation) -> None:
    """Verify get_thread() returns just root message when called on root.

    Requirements:
        - FR-278: Support retrieving conversation context for a message
        - Root message has no ancestors, thread should contain only itself

    Args:
        linear_conversation: Fixture with 3 messages (msg-1 is root)
    """
    thread = linear_conversation.get_thread("msg-1")

    assert len(thread) == 1, "Root message thread should contain only itself"
    assert thread[0].id == "msg-1", "Thread should contain the root message"


def test_get_thread_for_leaf_message(linear_conversation: Conversation) -> None:
    """Verify get_thread() returns full path from root to leaf.

    Requirements:
        - FR-278: Support retrieving conversation context for a message
        - Thread should be in chronological order (oldest first)

    Args:
        linear_conversation: Fixture with 3 messages (msg-1 -> msg-2 -> msg-3)
    """
    thread = linear_conversation.get_thread("msg-3")

    assert len(thread) == 3, "Leaf message should have full path to root"

    # Verify chronological order (oldest first)
    assert thread[0].id == "msg-1", "First message should be root"
    assert thread[1].id == "msg-2", "Second message should be middle"
    assert thread[2].id == "msg-3", "Third message should be leaf"

    # Verify parent-child relationships
    assert thread[0].parent_id is None, "Root has no parent"
    assert thread[1].parent_id == "msg-1", "msg-2 references msg-1"
    assert thread[2].parent_id == "msg-2", "msg-3 references msg-2"


def test_get_thread_for_mid_level_message(branching_conversation: Conversation) -> None:
    """Verify get_thread() returns partial path from root to mid-level message.

    Requirements:
        - FR-278: Support retrieving conversation context for a message
        - Thread should stop at target message, not include descendants

    Args:
        branching_conversation: Fixture with msg-1 -> msg-2 -> msg-4
    """
    thread = branching_conversation.get_thread("msg-2")

    assert len(thread) == 2, "Mid-level message should have path from root"
    assert thread[0].id == "msg-1", "First message should be root"
    assert thread[1].id == "msg-2", "Second message should be target"


def test_get_thread_for_non_existent_message(
    linear_conversation: Conversation,
) -> None:
    """Verify get_thread() returns empty list for non-existent message ID.

    Requirements:
        - FR-278: Support retrieving conversation context for a message
        - Graceful handling of invalid message IDs

    Args:
        linear_conversation: Fixture with 3 messages
    """
    thread = linear_conversation.get_thread("msg-non-existent")

    assert isinstance(thread, list), "get_thread() must return list"
    assert len(thread) == 0, "Non-existent message should return empty thread"


def test_get_thread_in_branching_conversation(
    branching_conversation: Conversation,
) -> None:
    """Verify get_thread() returns correct path in branching conversation.

    Requirements:
        - FR-278: Support retrieving conversation context for a message
        - Should follow parent_id chain, not siblings

    Args:
        branching_conversation: Fixture with branches at msg-1
    """
    # Get thread for msg-4 (in msg-1 -> msg-2 -> msg-4 branch)
    thread = branching_conversation.get_thread("msg-4")

    assert len(thread) == 3, "msg-4 should have 3-message thread"
    assert thread[0].id == "msg-1", "First message should be root"
    assert thread[1].id == "msg-2", "Second message should be msg-2"
    assert thread[2].id == "msg-4", "Third message should be msg-4"

    # Verify msg-3 (alternative branch) is NOT included
    thread_ids = {msg.id for msg in thread}
    assert "msg-3" not in thread_ids, "Alternative branch should not be included"


# ============================================================================
# T070-004: get_all_threads() Tests
# ============================================================================


def test_get_all_threads_with_single_message(
    single_message_conversation: Conversation,
) -> None:
    """Verify get_all_threads() returns single thread for single-message conversation.

    Requirements:
        - FR-280: Enable analysis of all conversation branches
        - Single message is both root and leaf, forms single thread

    Args:
        single_message_conversation: Fixture with 1 message
    """
    threads = single_message_conversation.get_all_threads()

    assert len(threads) == 1, "Single message should form 1 thread"
    assert len(threads[0]) == 1, "Thread should contain 1 message"
    assert threads[0][0].id == "msg-1", "Thread should contain the single message"


def test_get_all_threads_with_linear_conversation(
    linear_conversation: Conversation,
) -> None:
    """Verify get_all_threads() returns single thread for linear conversation.

    Requirements:
        - FR-280: Enable analysis of all conversation branches
        - Linear conversation has no branches, single root-to-leaf path

    Args:
        linear_conversation: Fixture with 3 messages in linear chain
    """
    threads = linear_conversation.get_all_threads()

    assert len(threads) == 1, "Linear conversation should have exactly 1 thread"

    thread = threads[0]
    assert len(thread) == 3, "Thread should contain all 3 messages"

    # Verify chronological order
    assert thread[0].id == "msg-1", "First message should be root"
    assert thread[1].id == "msg-2", "Second message should be middle"
    assert thread[2].id == "msg-3", "Third message should be leaf"


def test_get_all_threads_with_branching_conversation(
    branching_conversation: Conversation,
) -> None:
    """Verify get_all_threads() returns all branches in branching conversation.

    Requirements:
        - FR-280: Enable analysis of all conversation branches
        - Each root-to-leaf path should be a separate thread

    Args:
        branching_conversation: Fixture with 2 branches
    """
    threads = branching_conversation.get_all_threads()

    assert len(threads) == 2, "Branching conversation should have 2 threads"

    # Extract thread paths as ID sequences
    thread_paths = [tuple(msg.id for msg in thread) for thread in threads]

    # Expected threads (order may vary)
    expected_paths = {
        ("msg-1", "msg-2", "msg-4"),  # First branch
        ("msg-1", "msg-3"),  # Alternative branch
    }

    assert set(thread_paths) == expected_paths, "All branches should be captured"

    # Verify all threads start with root
    for thread in threads:
        assert thread[0].id == "msg-1", "All threads should start with root msg-1"


def test_get_all_threads_with_multi_root_conversation(
    multi_root_conversation: Conversation,
) -> None:
    """Verify get_all_threads() handles multiple root messages correctly.

    Requirements:
        - FR-280: Enable analysis of all conversation branches
        - Each root should have its own set of threads

    Args:
        multi_root_conversation: Fixture with 2 root messages
    """
    threads = multi_root_conversation.get_all_threads()

    assert len(threads) == 2, "Multi-root conversation should have 2 threads"

    # Extract thread paths
    thread_paths = [tuple(msg.id for msg in thread) for thread in threads]

    # Expected threads
    expected_paths = {
        ("msg-1", "msg-2"),  # First root's branch
        ("msg-3",),  # Second root (standalone)
    }

    assert set(thread_paths) == expected_paths, "All root branches should be captured"


def test_get_all_threads_with_complex_tree(
    complex_tree_conversation: Conversation,
) -> None:
    """Verify get_all_threads() handles complex multi-level branching.

    Requirements:
        - FR-280: Enable analysis of all conversation branches
        - Multiple branching levels should be fully traversed

    Args:
        complex_tree_conversation: Fixture with 3 distinct threads
    """
    threads = complex_tree_conversation.get_all_threads()

    assert len(threads) == 3, "Complex tree should have 3 distinct threads"

    # Extract thread paths
    thread_paths = [tuple(msg.id for msg in thread) for thread in threads]

    # Expected threads
    expected_paths = {
        ("msg-1", "msg-2", "msg-4", "msg-6"),  # Deep branch 1
        ("msg-1", "msg-2", "msg-5"),  # Deep branch 2
        ("msg-1", "msg-3"),  # Alternative branch
    }

    assert set(thread_paths) == expected_paths, "All complex branches should be captured"

    # Verify chronological order within each thread
    for thread in threads:
        timestamps = [msg.timestamp for msg in thread]
        assert timestamps == sorted(timestamps), "Messages within thread must be chronological"
