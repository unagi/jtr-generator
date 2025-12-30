import json
from pathlib import Path

import pytest

pytest.importorskip("fitz")

from tools.extract_lines import extract_lines_a3_to_a4x2

from skill.jtr.layout.anchors import resolve_texts_from_anchors

TOLERANCE_PT = 1.0


@pytest.fixture
def anchor_data():
    anchor_path = (
        Path(__file__).parent.parent / "fixtures/a4_text_anchors.json"
    )
    with open(anchor_path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def extracted_lines():
    pytest.importorskip("fitz")
    pdf_path = Path(__file__).parent.parent.parent / "tests/fixtures/R3_pdf_rirekisyo.pdf"
    return extract_lines_a3_to_a4x2(str(pdf_path))


def _assert_resolved_positions(anchor_texts, resolved_texts):
    assert len(anchor_texts) == len(resolved_texts)

    for anchor, resolved in zip(anchor_texts, resolved_texts, strict=True):
        assert anchor["text"] == resolved["text"]
        assert anchor["font_size"] == resolved["font_size"]
        assert anchor.get("align", "left") == resolved.get("align", "left")

        expected = anchor["reference_position"]
        dx = abs(resolved["x"] - expected["x"])
        dy = abs(resolved["y"] - expected["y"])
        assert dx <= TOLERANCE_PT and dy <= TOLERANCE_PT, (
            f"Text '{anchor['text']}' position mismatch: "
            f"expected ({expected['x']}, {expected['y']}), got ({resolved['x']}, {resolved['y']})"
        )


def test_page1_anchor_resolution(anchor_data, extracted_lines):
    resolved = resolve_texts_from_anchors(
        anchor_data["page1_texts"], extracted_lines["page1_lines"]
    )
    _assert_resolved_positions(anchor_data["page1_texts"], resolved)


def test_page2_anchor_resolution(anchor_data, extracted_lines):
    resolved = resolve_texts_from_anchors(
        anchor_data["page2_texts"], extracted_lines["page2_lines"]
    )
    _assert_resolved_positions(anchor_data["page2_texts"], resolved)
