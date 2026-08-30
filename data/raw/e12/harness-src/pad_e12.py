#!/usr/bin/env python3
"""pad_e12.py — real-code context pad of a TARGETED token length.

Builds a pad by measuring the REAL server tokenizer and returns the ACTUAL token count,
which every caller records; the >=90 %-of-window gate is evaluated on that actual count.

BUGFIX 2026-08-30 (pad-bisection defect, found while reviewing Wave 1):
  The previous build() bisected inside the FIXED bracket [0.9, 1.15] * cpt * target, where
  cpt was calibrated on text[:200_000]. This corpus is ~2.9 chars/token in its first 200 kB
  (dense django source) and ~4.45 chars/token thereafter, so for several targets the true
  cut lay OUTSIDE the bracket. The bisection then pinned at the bracket edge, assigned
  `best, best_n = t, n_tok` UNCONDITIONALLY (last probe, not closest), and returned short
  with no error: pad_201830 delivered 169,823 tokens (-15.9 %), which the Q4_K_XL sweep
  recorded as prefill_frac 0.797 while its own contract claims >=0.90.
  Fixes: (1) unbounded proportional seek — the e11 scheme, which converges regardless of how
  wrong cpt is; (2) keep the CLOSEST candidate, never the last; (3) RAISE if the result
  misses target by more than the tolerance; (4) validate cached pads on read and rebuild a
  stale/short one, so the bad pads already on disk self-heal.
"""
from pathlib import Path
import sys

sys.path.insert(0, "/srv/bench/e12/experiments")
import lib_e12 as L

REPO = Path("/srv/bench/champion-20260821/worktrees/django-37278-prefix")
SUFFIXES = {".py", ".rst", ".txt", ".md", ".toml"}

NEEDLES = [
    (0.10, "E11_ALPHA_4F27", "# AUDIT FACT\nThe alpha audit marker is E11_ALPHA_4F27.\n"),
    (0.50, "E11_MID_9C31",   "# AUDIT FACT\nThe middle audit marker is E11_MID_9C31.\n"),
    (0.90, "E11_OMEGA_7B58", "# AUDIT FACT\nThe omega audit marker is E11_OMEGA_7B58.\n"),
]

CORPUS_CACHE = Path("/srv/bench/e12/corpus.txt")
PAD_DIR = Path("/srv/bench/e12/pads")

# A pad may miss its target by at most max(TOL_ABS, TOL_FRAC * target) tokens.
TOL_ABS = 64
TOL_FRAC = 0.005          # 0.5 % — far tighter than the 0.90 window gate it must satisfy


def _raw_text(min_chars):
    if CORPUS_CACHE.exists() and CORPUS_CACHE.stat().st_size >= min_chars:
        return CORPUS_CACHE.read_text(errors="replace")
    files = [p for p in sorted(REPO.rglob("*"))
             if p.is_file() and ".git" not in p.parts and p.suffix in SUFFIXES]
    assert files, f"no source files under {REPO}"
    out, n, pas = [], 0, 0
    while n < min_chars:
        pas += 1
        for p in files:
            try:
                t = p.read_text(errors="replace")
            except OSError:
                continue
            chunk = f"\n\n===== PASS {pas}: {p.relative_to(REPO)} =====\n{t}"
            out.append(chunk)
            n += len(chunk)
            if n >= min_chars:
                break
    txt = "".join(out)
    CORPUS_CACHE.write_text(txt)
    return txt


def _mk(text, cut, with_needles):
    """Cut the corpus to `cut` chars and (optionally) plant the needles at their depths.
    Needles are inserted BEFORE tokenizing so their tokens are inside the measured count."""
    t = text[:cut]
    if not with_needles:
        return t
    n = len(t)
    pieces, last = [], 0
    for frac, _code, snip in NEEDLES:
        pos = int(n * frac)
        nl = t.find("\n", pos)              # land on a line boundary
        pos = nl + 1 if nl != -1 else pos
        pos = max(pos, last)
        pieces.append(t[last:pos])
        pieces.append(snip)
        last = pos
    pieces.append(t[last:])
    return "".join(pieces)


def tolerance(target_tokens):
    return max(TOL_ABS, int(target_tokens * TOL_FRAC))


def build(target_tokens, with_needles=False):
    """Return (text, exact_token_count). Raises RuntimeError if it cannot hit the target."""
    if target_tokens <= 0:
        return "", 0
    tol = tolerance(target_tokens)
    PAD_DIR.mkdir(parents=True, exist_ok=True)
    cache = PAD_DIR / f"pad_{target_tokens}_{int(with_needles)}.txt"
    if cache.exists():
        t = cache.read_text(errors="replace")
        n = len(L.tokenize(t))
        if abs(n - target_tokens) <= tol:
            return t, n
        # a cached pad that misses its own target is the bisection defect — rebuild it
        bad = cache.with_name(cache.name + f".bad-{n}")
        cache.rename(bad)
        print(f"pad_e12: cached {cache.name} is {n} tokens vs target {target_tokens} "
              f"(tol {tol}) — quarantined to {bad.name}, rebuilding", flush=True)

    text = _raw_text(target_tokens * 8)
    sample = text[:200000]
    cpt = len(sample) / max(1, len(L.tokenize(sample)))
    cut = min(len(text), max(1000, int(target_tokens * cpt)))
    best = None                                   # (text, n_tok, cut) — CLOSEST, not last
    for _ in range(12):
        t = _mk(text, cut, with_needles)
        n = len(L.tokenize(t))
        if best is None or abs(n - target_tokens) < abs(best[1] - target_tokens):
            best = (t, n, cut)
        if abs(n - target_tokens) <= tol:
            break
        nxt = max(1000, min(len(text), int(cut * target_tokens / max(1, n))))
        if nxt == cut:
            break                                 # proportional step stalled
        cut = nxt

    t, n, cut = best
    if abs(n - target_tokens) > tol:
        raise RuntimeError(
            f"pad_e12.build: could not reach {target_tokens} tokens (best {n} at {cut} chars "
            f"of {len(text)}, tol {tol}). Corpus exhausted or tokenizer unavailable — refusing "
            f"to return a short pad (a short pad silently understates prefill depth).")
    cache.write_text(t)
    return t, n
