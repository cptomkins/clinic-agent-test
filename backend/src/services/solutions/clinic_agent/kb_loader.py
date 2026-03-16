# backend/src/services/solutions/clinic_agent/kb_loader.py
# Author: Claude
# Created Date: 2026-03-15
# v0.12.0 — Knowledge base loader with keyword search
from __future__ import annotations

import os
import re
import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Path to knowledge base markdown files ────────────────────

KB_DIR = Path(__file__).resolve().parent.parent.parent.parent / "knowledge_bases" / "clinic_agent"

# ── Data structures ──────────────────────────────────────────


@dataclass
class KBChunk:
    """A single searchable chunk from the knowledge base."""
    source_file: str       # e.g. "scheduling.md"
    heading: str           # e.g. "Booking an Appointment"
    content: str           # full text under that heading
    tokens: list[str] = field(default_factory=list, repr=False)


# ── Loader ───────────────────────────────────────────────────

_chunks: list[KBChunk] | None = None


def _split_by_heading(text: str, source_file: str) -> list[KBChunk]:
    """Split markdown text into chunks by ## headings.

    Each chunk contains the heading and all content until the next heading
    of equal or higher level. The top-level # heading is treated as metadata
    and prepended to the first chunk only.
    """
    lines = text.split("\n")
    chunks: list[KBChunk] = []
    current_heading = ""
    current_lines: list[str] = []
    file_title = ""

    for line in lines:
        # Top-level title (# Heading)
        if re.match(r"^# [^#]", line):
            file_title = line.lstrip("# ").strip()
            continue

        # Section heading (## or ###)
        if re.match(r"^#{2,3} ", line):
            # Save previous chunk
            if current_heading and current_lines:
                content = "\n".join(current_lines).strip()
                if content:
                    chunks.append(KBChunk(
                        source_file=source_file,
                        heading=current_heading,
                        content=content,
                    ))
            current_heading = line.lstrip("#").strip()
            current_lines = []
        else:
            current_lines.append(line)

    # Save last chunk
    if current_heading and current_lines:
        content = "\n".join(current_lines).strip()
        if content:
            chunks.append(KBChunk(
                source_file=source_file,
                heading=current_heading,
                content=content,
            ))

    # If no headings found, treat entire file as one chunk
    if not chunks and text.strip():
        chunks.append(KBChunk(
            source_file=source_file,
            heading=file_title or source_file,
            content=text.strip(),
        ))

    return chunks


STOP_WORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "can", "shall", "to", "of", "in", "for",
    "on", "with", "at", "by", "from", "as", "into", "about", "between",
    "through", "after", "before", "above", "below", "and", "but", "or",
    "not", "no", "nor", "so", "if", "then", "than", "that", "this",
    "these", "those", "it", "its", "i", "me", "my", "we", "our", "you",
    "your", "he", "she", "they", "them", "what", "which", "who", "how",
    "when", "where", "why", "all", "each", "any", "both", "more", "most",
    "some", "such", "up", "out", "just", "also", "very", "too", "here",
    "there", "am", "get", "go", "see", "need", "want", "find", "help",
}


def _tokenize(text: str) -> list[str]:
    """Simple lowercase word tokenization with stop word removal."""
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [w for w in words if w not in STOP_WORDS]


def _load_chunks() -> list[KBChunk]:
    """Load and parse all markdown files in the KB directory."""
    global _chunks
    if _chunks is not None:
        return _chunks

    _chunks = []
    if not KB_DIR.exists():
        logger.warning(f"Knowledge base directory not found: {KB_DIR}")
        return _chunks

    md_files = sorted(KB_DIR.rglob("*.md"))
    logger.info(f"KB loader: scanning {KB_DIR} — found {len(md_files)} files: {[f.name for f in md_files]}")

    for md_file in md_files:
        text = md_file.read_text(encoding="utf-8")
        file_chunks = _split_by_heading(text, md_file.name)
        for chunk in file_chunks:
            chunk.tokens = _tokenize(f"{chunk.heading} {chunk.content}")
        _chunks.extend(file_chunks)

    logger.info(f"Loaded {len(_chunks)} KB chunks from {KB_DIR}")
    return _chunks


def reload_chunks() -> None:
    """Force reload of knowledge base (useful for testing)."""
    global _chunks
    _chunks = None
    _load_chunks()


# ── Search ───────────────────────────────────────────────────


def search_kb(query: str, max_results: int = 3) -> list[dict]:
    """Search knowledge base chunks using keyword matching with BM25-style scoring.

    Args:
        query: Natural language search query.
        max_results: Maximum number of results to return.

    Returns:
        List of dicts with keys: source_file, heading, content, score.
    """
    chunks = _load_chunks()
    if not chunks:
        return []

    query_tokens = set(_tokenize(query))
    if not query_tokens:
        return []

    scored: list[tuple[float, KBChunk]] = []

    for chunk in chunks:
        chunk_token_set = set(chunk.tokens)
        # Count matching unique query terms
        matching_terms = query_tokens & chunk_token_set
        if not matching_terms:
            continue

        # Score: weighted by number of matching terms + frequency boost
        term_coverage = len(matching_terms) / len(query_tokens)
        freq_score = sum(
            chunk.tokens.count(t) for t in matching_terms
        ) / max(len(chunk.tokens), 1)

        # Heading match bonus — if query terms appear in heading, boost
        heading_tokens = set(_tokenize(chunk.heading))
        heading_overlap = len(query_tokens & heading_tokens)
        heading_bonus = heading_overlap * 0.5

        score = term_coverage + freq_score + heading_bonus
        scored.append((score, chunk))

    # Sort by score descending
    scored.sort(key=lambda x: x[0], reverse=True)

    results = []
    for score, chunk in scored[:max_results]:
        results.append({
            "source_file": chunk.source_file,
            "heading": chunk.heading,
            "content": chunk.content,
            "score": round(score, 3),
        })

    return results
