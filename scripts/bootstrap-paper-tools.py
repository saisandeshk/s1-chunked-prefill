#!/usr/bin/env python3
"""Install a pinned workstation TeX compiler in the ignored project cache."""

import hashlib
import io
from pathlib import Path
import platform
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
URL = "https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%400.17.0/tectonic-0.17.0-x86_64-unknown-linux-musl.tar.gz"
ARCHIVE_SHA256 = "8533d07f9ccbd7a65824b9e0459041bca34af1eb33daba48f59215593753a3b7"
BINARY_SHA256 = "a98aa59ad5c1df39a6c9e56cbfc5088f2b11d6c179c0130b97998e4bd46a46da"


def main():
    if platform.system() != "Linux" or platform.machine() != "x86_64":
        raise SystemExit("This pinned paper tool is for the x86_64 Linux workstation")
    target = ROOT / "cache/tools/tectonic"
    if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() == BINARY_SHA256:
        print(target)
        return
    data = urllib.request.urlopen(URL, timeout=120).read()
    if hashlib.sha256(data).hexdigest() != ARCHIVE_SHA256:
        raise SystemExit("Tectonic archive checksum mismatch")
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
        member = archive.getmember("tectonic")
        if not member.isfile():
            raise SystemExit("Unexpected Tectonic archive member")
        binary = archive.extractfile(member).read()
    if hashlib.sha256(binary).hexdigest() != BINARY_SHA256:
        raise SystemExit("Tectonic executable checksum mismatch")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(binary)
    target.chmod(0o755)
    print(target)


if __name__ == "__main__":
    main()
