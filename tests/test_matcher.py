"""Tests for phone matcher precision, recall, and false positive avoidance."""

import pytest
from backend.app.engines.discovery.normalizer import parse_and_normalize
from backend.app.engines.discovery.matcher import match_phone_in_text, sanitize_html_to_text


@pytest.fixture
def target_phone():
    return parse_and_normalize("+14155552671", "US")


def test_exact_match_in_html(target_phone):
    html = """
    <html>
      <body>
        <div class="profile">
          <h2>Contact Person</h2>
          <p>Direct line: <strong>+1 415-555-2671</strong> for urgent inquiries.</p>
        </div>
      </body>
    </html>
    """
    res = match_phone_in_text(html, target_phone)
    assert res.matched is True
    assert res.match_type == "EXACT"
    assert res.confidence == 1.0
    assert "+1 415-555-2671" in res.matched_text
    assert "Direct line:" in res.snippet


def test_probable_match_dashed(target_phone):
    text = "Call Jane at 415-555-2671 regarding the apartment sublet."
    res = match_phone_in_text(text, target_phone)
    assert res.matched is True
    assert res.match_type in ("EXACT", "PROBABLE")
    assert res.confidence >= 0.8


def test_false_positive_rejection_date(target_phone):
    # A date like 2024-05-18 or similar numbers shouldn't match
    text = "Release date was 2024-05-18 and build number 2024051801."
    res = match_phone_in_text(text, target_phone)
    assert res.matched is False or res.match_type == "FALSE_POSITIVE"


def test_false_positive_rejection_uuid(target_phone):
    text = "Transaction ID: 14155552-6710-4000-8000-000000000000 completed successfully."
    res = match_phone_in_text(text, target_phone)
    assert res.match_type in ("NONE", "FALSE_POSITIVE")
    assert res.confidence < 0.5


def test_html_sanitization_strips_scripts():
    raw_html = "<script>alert('xss')</script><style>body {color:red}</style><p>Hello World 415-555-2671</p>"
    clean = sanitize_html_to_text(raw_html)
    assert "<script>" not in clean
    assert "alert" not in clean
    assert "<style>" not in clean
    assert "Hello World 415-555-2671" in clean


@pytest.mark.parametrize("text,expected", [
    ("Call 92465 79002 for details", ("EXACT", "PROBABLE")),
    ("Mobile: +91-9246579002", ("EXACT", "PROBABLE")),
    ("Contact Support +91-09246579002", ("EXACT",)),
    ("Ph: 092465-79002", ("EXACT",)),
    ("(+91) 92465-79002", ("EXACT", "PROBABLE")),
])
def test_indian_local_formats_match(text, expected):
    phone = parse_and_normalize("+919246579002", "IN")
    res = match_phone_in_text(text, phone)
    assert res.matched is True
    assert res.match_type in expected


def test_indian_landline_std_format_matches():
    phone = parse_and_normalize("+911126769666", "IN")
    res = match_phone_in_text("Delhi office: 011-26769666, Kolkata 033-22361401", phone)
    assert res.matched is True and res.match_type == "EXACT"


def test_other_country_code_with_same_digits_is_not_matched():
    phone = parse_and_normalize("+919246579002", "IN")
    res = match_phone_in_text("US line +1 924 657 9002 only", phone)
    assert res.match_type != "EXACT"


def test_snippet_never_contains_raw_number():
    phone = parse_and_normalize("+919246579002", "IN")
    res = match_phone_in_text("Contact Info +91- 92465 79002 Address Etawah", phone)
    assert res.matched
    assert "92465 79002" not in res.snippet and "9246579002" not in res.snippet
    assert "••" in res.snippet
