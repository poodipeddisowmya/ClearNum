"""Context-aware phone number matcher.
Evaluates textual evidence against normalized phone variants and classifies matches
into EXACT, PROBABLE, WEAK, or FALSE_POSITIVE tiers with sanitized snippets.
"""

import re
from dataclasses import dataclass
from typing import Optional, Tuple
import html
import unicodedata
from bs4 import BeautifulSoup
from backend.app.engines.discovery.normalizer import NormalizedPhone


@dataclass
class MatchResult:
    matched: bool
    match_type: str  # "EXACT", "PROBABLE", "WEAK", "FALSE_POSITIVE"
    confidence: float  # 0.0 to 1.0
    matched_text: str
    snippet: str


# Regexes to detect common false positive sequences (dates, UUIDs, ISBNs, tracking numbers)
DATE_PATTERN = re.compile(r"\b(?:19|20)\d{2}[-/.]\d{2}[-/.]\d{2}\b")
UUID_PATTERN = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")
ISBN_PATTERN = re.compile(r"\b(?:978|979)[- ]?\d{1,5}[- ]?\d{1,7}[- ]?\d{1,7}[- ]?\d\b")


def sanitize_html_to_text(html_content: str) -> str:
    """Safely extracts clean plain text from HTML, stripping all script,
    style, and markup elements, decoding HTML entities, and normalizing
    Unicode characters (NFKC) to prevent evasion and false negatives.
    """
    if not html_content:
        return ""
    # Decode HTML entities (e.g. &#43;1-415-555-2671 -> +1-415-555-2671)
    unescaped = html.unescape(html_content)
    # NFKC normalizes fullwidth characters (e.g. ＋１４１５５５５２６７１ -> +14155552671)
    normalized = unicodedata.normalize("NFKC", unescaped)
    try:
        soup = BeautifulSoup(normalized, "html.parser")
        for tag in soup(["script", "style", "noscript", "header", "footer"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        return re.sub(r"\s+", " ", text)
    except Exception:
        # Fallback regex tag stripping
        clean = re.sub(r"<[^>]+>", " ", normalized)
        return re.sub(r"\s+", " ", clean).strip()


def extract_context_snippet(text: str, match_start: int, match_end: int, window: int = 100) -> str:
    """Extracts a bounded text snippet surrounding the matched index."""
    start = max(0, match_start - window)
    end = min(len(text), match_end + window)
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(text) else ""
    return f"{prefix}{text[start:end].strip()}{suffix}"


PHONE_RUN_PATTERN = re.compile(r"(?:\+|00)?[\d(][\d\s().\-]{5,}\d")


def _match_grouped_digits(clean_text: str, phone: NormalizedPhone) -> Optional[MatchResult]:
    """Finds the number however its digit groups are separated, by joining
    consecutive groups of each phone-like run and comparing the digits."""
    cc = str(phone.country_code)
    nat = phone.digits_only[len(cc):] if phone.digits_only.startswith(cc) else ""
    if len(nat) < 7:
        return None
    # digits -> (match_type, confidence); trunk-prefixed and +cc forms are unambiguous
    targets = {
        cc + nat: ("EXACT", 0.95),
        cc + "0" + nat: ("EXACT", 0.95),
        "0" + nat: ("EXACT", 0.95),
        nat: ("PROBABLE", 0.8),
    }
    for run in PHONE_RUN_PATTERN.finditer(clean_text):
        groups = [(m.start() + run.start(), m.end() + run.start(), m.group(0))
                  for m in re.finditer(r"\d+", run.group(0))]
        has_plus = run.group(0).startswith(("+", "00"))
        for i in range(len(groups)):
            if i == 1 and has_plus:
                continue  # first group was a (different) country code
            joined = ""
            for j in range(i, len(groups)):
                joined += groups[j][2]
                if len(joined) > len(cc) + len(nat) + 1:
                    break
                hit = targets.get(joined)
                if not hit:
                    continue
                start, end = groups[i][0], groups[j][1]
                snippet = extract_context_snippet(clean_text, start, end)
                if DATE_PATTERN.search(clean_text[start:end]) or UUID_PATTERN.search(snippet):
                    continue
                return MatchResult(True, hit[0], hit[1], clean_text[start:end], snippet)
    return None


def mask_phone_in_text(text: str, phone: NormalizedPhone, extra: str = "") -> str:
    """Masks every known spelling of the target number in free text (snippets, titles),
    so evidence can be stored and shown without the raw number."""
    if not text or not phone.is_possible:
        return text or ""
    from backend.app.core.security import mask_phone_number
    cc = str(phone.country_code)
    nat = phone.digits_only[len(cc):] if phone.digits_only.startswith(cc) else ""
    variants = {extra, phone.e164, phone.international, phone.national, phone.dashed,
                phone.dotted, phone.spaced, phone.digits_only, nat}
    for v in sorted((v for v in variants if v and len(v) >= 7), key=len, reverse=True):
        text = text.replace(v, mask_phone_number(phone.e164))
    return text


def match_phone_in_text(text: str, phone: NormalizedPhone) -> MatchResult:
    """Analyzes a block of plain text or HTML for appearances of the target phone number.
    Returns a MatchResult whose snippet has the number masked (raw digits stay in matched_text only).
    """
    res = _match_phone_in_text_raw(text, phone)
    if res.snippet:
        res.snippet = mask_phone_in_text(res.snippet, phone, res.matched_text)
    return res


def _match_phone_in_text_raw(text: str, phone: NormalizedPhone) -> MatchResult:
    clean_text = sanitize_html_to_text(text)
    if not clean_text or not phone.is_possible:
        return MatchResult(
            matched=False,
            match_type="NONE",
            confidence=0.0,
            matched_text="",
            snippet="",
        )
    
    # 1. Check for EXACT matches (E.164, strict national, international)
    exact_candidates = [
        phone.e164,
        phone.international,
        phone.national,
        phone.dashed,
        phone.dotted,
    ]
    
    for candidate in exact_candidates:
        if candidate and candidate in clean_text:
            idx = clean_text.find(candidate)
            snippet = extract_context_snippet(clean_text, idx, idx + len(candidate))
            
            # Verify it is not part of a date or UUID
            if DATE_PATTERN.search(snippet) and len(candidate) <= 10:
                # Could be a date false positive
                pass
            else:
                return MatchResult(
                    matched=True,
                    match_type="EXACT",
                    confidence=1.0,
                    matched_text=candidate,
                    snippet=snippet,
                )
    
    # 2. Check for spaced or unpunctuated format
    spaced_candidate = phone.spaced
    if spaced_candidate and spaced_candidate in clean_text:
        idx = clean_text.find(spaced_candidate)
        snippet = extract_context_snippet(clean_text, idx, idx + len(spaced_candidate))
        return MatchResult(
            matched=True,
            match_type="PROBABLE",
            confidence=0.85,
            matched_text=spaced_candidate,
            snippet=snippet,
        )
        
    # 3. Check for digits only sequence bounded by word boundaries
    if phone.digits_only and len(phone.digits_only) >= 10:
        pattern = re.compile(rf"(?<!\d){re.escape(phone.digits_only)}(?!\d)")
        match = pattern.search(clean_text)
        if match:
            idx = match.start()
            snippet = extract_context_snippet(clean_text, idx, match.end())
            # Check false positives
            if UUID_PATTERN.search(snippet) or ISBN_PATTERN.search(snippet):
                return MatchResult(
                    matched=False,
                    match_type="FALSE_POSITIVE",
                    confidence=0.0,
                    matched_text=match.group(0),
                    snippet=snippet,
                )
            return MatchResult(
                matched=True,
                match_type="PROBABLE",
                confidence=0.75,
                matched_text=match.group(0),
                snippet=snippet,
            )
            
    # Grouped-digit match ("+91-9246579002", "011-26769666"); unambiguous forms win over the weak check
    grouped = _match_grouped_digits(clean_text, phone)
    if grouped and grouped.match_type == "EXACT":
        return grouped

    # 4. Weak match: national digits without country code
    national_digits = phone.digits_only[len(str(phone.country_code)):] if len(phone.digits_only) > 10 else phone.digits_only
    if national_digits and len(national_digits) >= 10:
        pattern = re.compile(rf"(?<!\d){re.escape(national_digits)}(?!\d)")
        match = pattern.search(clean_text)
        if match:
            idx = match.start()
            snippet = extract_context_snippet(clean_text, idx, match.end())
            return MatchResult(
                matched=True,
                match_type="WEAK",
                confidence=0.45,
                matched_text=match.group(0),
                snippet=snippet,
            )

    # 5. Grouped national digits in any local style: "94112 74848"
    if grouped:
        return grouped

    return MatchResult(
        matched=False,
        match_type="NONE",
        confidence=0.0,
        matched_text="",
        snippet="",
    )
