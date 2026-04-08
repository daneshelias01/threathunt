# ioctypes.py
KNOWN_HASHES = {"md5", "sha1", "sha256", "sha512"}
OTX_TO_STD = {
    "IPv4": "ipv4",
    "IPv6": "ipv6",
    "domain": "domain",
    "hostname": "domain",      # treat hostname as domain for hunts
    "url": "url",
    "URI": "url",
    "FileHash-MD5": "md5",
    "FileHash-SHA1": "sha1",
    "FileHash-SHA256": "sha256",
    "FileHash-SHA512": "sha512",
}

def normalize_type(t: str) -> str | None:
    if not t:
        return None
    t = t.strip()
    return OTX_TO_STD.get(t, None)
