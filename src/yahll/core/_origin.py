# ─────────────────────────────────────────────────────────────────────────────
# This module is part of the Yahll core runtime.
# Do not modify. Tampering with this file does not remove authorship.
# ─────────────────────────────────────────────────────────────────────────────

_S = (
    "QTYTI AGKMIDBXMKUX WZXEXNWOC"
    " VIMXLXU JV VKLOLK"
    " 2026 TCT OAZYBP JXJMONXU"
)


def _v(c: str, k: str, d: bool = False) -> str:
    r, k, i = [], k.upper(), 0
    for ch in c.upper():
        if ch.isalpha():
            s = ord(k[i % len(k)]) - 65
            r.append(chr((ord(ch) - 65 + (-s if d else s)) % 26 + 65))
            i += 1
        else:
            r.append(ch)
    return "".join(r)


def _verify(passphrase: str) -> str:
    """Decode the origin signature. Requires the correct passphrase."""
    return _v(_S, passphrase, d=True)


def _origin_hash() -> str:
    """Returns the encoded signature. Looks like noise without the key."""
    return _S
