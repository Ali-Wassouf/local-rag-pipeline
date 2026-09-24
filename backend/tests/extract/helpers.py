"""Shared Block IR contract checks, run against every extractor's output."""

from app.extract.base import Block


def assert_valid_blocks(blocks: list[Block]) -> None:
    for block in blocks:
        assert isinstance(block, dict), f"block leaked a non-dict type: {block!r}"
        assert block["text"].strip(), f"empty block text: {block!r}"
        if block["type"] == "heading":
            level = block["level"]
            assert level is not None and 1 <= level <= 6, (
                f"heading block has invalid level: {block!r}"
            )
        else:
            assert block["level"] is None, f"non-heading block has a level: {block!r}"
        assert isinstance(block["anchor"], int), f"anchor is not an int: {block!r}"
