#!/usr/bin/env bash
#
# Search-Then-Export Pipeline Workflow
#
# This example demonstrates the echomine CLI pipeline workflow where users:
# 1. Search for conversations by keyword, title, or date range
# 2. Extract conversation IDs from JSON output using jq
# 3. Export matching conversations to markdown files
#
# Requirements:
#   - echomine installed and available in PATH
#   - jq (JSON processor) for extracting conversation IDs
#   - Valid OpenAI conversation export JSON file
#
# Example Usage:
#   # Search for all conversations about "Python" and export to markdown
#   ./examples/search_then_export.sh export.json "python" output_dir/
#
#   # Search by title and date range
#   ./examples/search_then_export.sh export.json "algorithm" output_dir/ \
#       --title "LeetCode" --from-date 2024-01-01 --to-date 2024-12-31
#
#   # Search with custom limit
#   ./examples/search_then_export.sh export.json "machine learning" output_dir/ --limit 5
#
# Architecture Compliance:
#   - Principle II (CLI Interface Contract): Demonstrates stdout/stderr separation
#   - FR-356 to FR-360: Search-then-export pipeline workflow
#   - FR-301 to FR-306: JSON output with conversation IDs for pipeline composition
#   - Pipeline-friendly: Composable with jq, xargs, and other Unix tools
#
# Performance Characteristics:
#   - Memory: O(1) per conversation (streaming search and export)
#   - Processing: Sequential export (can be parallelized with xargs -P)
#   - Output: One markdown file per conversation

set -euo pipefail  # Exit on error, undefined variables, and pipe failures

# Color codes for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages to stderr
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*" >&2
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*" >&2
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

# Function to display usage information
usage() {
    cat <<EOF
Usage: $0 <export_file> <keywords> <output_dir> [OPTIONS]

Arguments:
    export_file    Path to OpenAI conversation export JSON file
    keywords       Keywords to search for (space-separated, quoted)
    output_dir     Directory to save exported markdown files

Options:
    --title TEXT        Filter by conversation title (case-insensitive)
    --from-date DATE    Filter from date (YYYY-MM-DD format)
    --to-date DATE      Filter to date (YYYY-MM-DD format)
    --limit N           Limit number of results to export

Examples:
    # Search for "Python" conversations and export all matches
    $0 export.json "python" output_dir/

    # Search with title filter
    $0 export.json "algorithm" output_dir/ --title "LeetCode"

    # Search with date range (last quarter of 2024)
    $0 export.json "AI" output_dir/ --from-date 2024-10-01 --to-date 2024-12-31

    # Limit to top 5 results
    $0 export.json "machine learning" output_dir/ --limit 5

Requirements:
    - echomine CLI installed (pip install -e .)
    - jq JSON processor (brew install jq or apt-get install jq)
EOF
    exit 2
}

# Validate dependencies
check_dependencies() {
    local missing_deps=()

    if ! command -v echomine &> /dev/null; then
        missing_deps+=("echomine (install with: pip install -e .)")
    fi

    if ! command -v jq &> /dev/null; then
        missing_deps+=("jq (install with: brew install jq or apt-get install jq)")
    fi

    if [ ${#missing_deps[@]} -gt 0 ]; then
        log_error "Missing required dependencies:"
        for dep in "${missing_deps[@]}"; do
            log_error "  - $dep"
        done
        exit 1
    fi
}

# Parse command-line arguments
parse_args() {
    if [ $# -lt 3 ]; then
        log_error "Insufficient arguments"
        usage
    fi

    EXPORT_FILE="$1"
    KEYWORDS="$2"
    OUTPUT_DIR="$3"
    shift 3

    # Optional arguments
    SEARCH_OPTS=()
    while [ $# -gt 0 ]; do
        case "$1" in
            --title)
                SEARCH_OPTS+=(--title "$2")
                shift 2
                ;;
            --from-date)
                SEARCH_OPTS+=(--from-date "$2")
                shift 2
                ;;
            --to-date)
                SEARCH_OPTS+=(--to-date "$2")
                shift 2
                ;;
            --limit)
                SEARCH_OPTS+=(--limit "$2")
                shift 2
                ;;
            *)
                log_error "Unknown option: $1"
                usage
                ;;
        esac
    done
}

# Validate input file and output directory
validate_inputs() {
    # Check if export file exists
    if [ ! -f "$EXPORT_FILE" ]; then
        log_error "Export file not found: $EXPORT_FILE"
        exit 1
    fi

    # Create output directory if it doesn't exist
    if [ ! -d "$OUTPUT_DIR" ]; then
        log_info "Creating output directory: $OUTPUT_DIR"
        mkdir -p "$OUTPUT_DIR"
    fi
}

# Step 1: Search for conversations matching criteria
search_conversations() {
    log_info "Searching conversations in $EXPORT_FILE..."
    log_info "Keywords: $KEYWORDS"
    if [ ${#SEARCH_OPTS[@]} -gt 0 ]; then
        log_info "Additional filters: ${SEARCH_OPTS[*]}"
    fi

    # Run search command with JSON output (results to stdout, progress to stderr)
    # The --format json flag ensures machine-readable output with conversation IDs
    local search_results
    search_results=$(echomine search "$EXPORT_FILE" \
        --keywords "$KEYWORDS" \
        --format json \
        "${SEARCH_OPTS[@]}" 2>&1 >/dev/stdout | tee /dev/stderr) || {
        local exit_code=$?
        if [ $exit_code -eq 130 ]; then
            log_warning "Search interrupted by user (Ctrl+C)"
        else
            log_error "Search failed with exit code $exit_code"
        fi
        exit $exit_code
    }

    echo "$search_results"
}

# Step 2: Extract conversation IDs from JSON search results
extract_conversation_ids() {
    local search_json="$1"

    # Use jq to extract conversation IDs from the results array
    # The search command returns JSON in format: {"results": [...], "metadata": {...}}
    # Each result has: {"conversation_id": "...", "title": "...", "score": ...}
    echo "$search_json" | jq -r '.results[].conversation_id' 2>/dev/null || {
        log_error "Failed to parse search results JSON"
        log_error "Expected format: {\"results\": [{\"conversation_id\": \"...\", ...}], \"metadata\": {...}}"
        return 1
    }
}

# Step 3: Export each conversation to markdown
export_conversations() {
    local -a conversation_ids=("$@")
    local count=${#conversation_ids[@]}

    if [ $count -eq 0 ]; then
        log_warning "No conversations found matching search criteria"
        log_info "Try broadening your search filters or keywords"
        exit 0
    fi

    log_success "Found $count conversation(s) to export"
    log_info "Exporting to directory: $OUTPUT_DIR"

    local success_count=0
    local failure_count=0

    # Export each conversation to a separate markdown file
    for i in "${!conversation_ids[@]}"; do
        local conv_id="${conversation_ids[$i]}"
        local output_file="$OUTPUT_DIR/${conv_id}.md"
        local progress=$((i + 1))

        log_info "[$progress/$count] Exporting conversation: $conv_id"

        # Export conversation to markdown file
        # The export command supports both stdout and file output via --output
        if echomine export "$EXPORT_FILE" "$conv_id" --output "$output_file" 2>&1; then
            ((success_count++))
            log_success "  -> Saved to: $output_file"
        else
            ((failure_count++))
            log_error "  -> Failed to export conversation: $conv_id"
        fi
    done

    # Summary statistics
    echo ""
    log_success "Export complete!"
    log_info "Successfully exported: $success_count/$count conversations"
    if [ $failure_count -gt 0 ]; then
        log_warning "Failed to export: $failure_count conversations"
    fi
}

# Main workflow
main() {
    # Validate environment
    check_dependencies

    # Parse and validate inputs
    parse_args "$@"
    validate_inputs

    log_info "=== Echomine Search-Then-Export Pipeline ==="
    echo ""

    # Step 1: Search for matching conversations
    log_info "Step 1/3: Searching conversations..."
    local search_results
    search_results=$(search_conversations)

    # Validate search returned valid JSON
    if [ -z "$search_results" ] || ! echo "$search_results" | jq empty 2>/dev/null; then
        log_error "Search did not return valid JSON output"
        exit 1
    fi

    echo ""

    # Step 2: Extract conversation IDs
    log_info "Step 2/3: Extracting conversation IDs..."
    local conversation_ids
    mapfile -t conversation_ids < <(extract_conversation_ids "$search_results")

    if [ $? -ne 0 ]; then
        exit 1
    fi

    echo ""

    # Step 3: Export to markdown
    log_info "Step 3/3: Exporting conversations to markdown..."
    export_conversations "${conversation_ids[@]}"

    echo ""
    log_success "=== Pipeline complete! ==="
    log_info "Output directory: $OUTPUT_DIR"
}

# Run main workflow
main "$@"