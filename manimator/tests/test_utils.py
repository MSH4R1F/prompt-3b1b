"""Unit tests for pipeline.utils."""

import pytest

from pipeline.utils import strip_markdown_fences


def test_no_fences_returns_text_unchanged():
    text = '{"key": "value"}'
    assert strip_markdown_fences(text) == text


def test_json_tagged_fence():
    text = '```json\n{"key": "value"}\n```'
    assert strip_markdown_fences(text) == '{"key": "value"}'


def test_plain_fence():
    text = "```\nhello\n```"
    assert strip_markdown_fences(text) == "hello"


def test_trailing_text_after_closing_fence():
    text = '```json\n{"key": "value"}\n```\nSome explanation here.'
    assert strip_markdown_fences(text) == '{"key": "value"}'


def test_strips_surrounding_whitespace():
    text = '  ```json\n{"key": "value"}\n```  '
    assert strip_markdown_fences(text) == '{"key": "value"}'


def test_fence_with_no_newline_returns_empty():
    assert strip_markdown_fences("```") == ""


def test_multiline_content_preserved():
    text = "```json\n{\n  \"a\": 1,\n  \"b\": 2\n}\n```"
    assert strip_markdown_fences(text) == '{\n  "a": 1,\n  "b": 2\n}'
