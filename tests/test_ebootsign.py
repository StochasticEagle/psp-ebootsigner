#!/usr/bin/env python3

import hashlib
import pathlib
import struct
import subprocess
import sys
import tempfile


PBP_HEADER_SIZE = 40
SIGNED_PSP_SIZE = 0x553450


def make_minimal_prx():
    data = bytearray(52)

    # Minimal ELF32 header accepted by fix_realocations(). The signer only
    # requires the PSP PRX e_type and a structurally valid section count.
    data[0:4] = b"\x7fELF"
    data[4] = 1
    data[5] = 1
    data[6] = 1

    struct.pack_into("<H", data, 16, 0xFFA0)
    struct.pack_into("<H", data, 18, 8)
    struct.pack_into("<I", data, 20, 1)
    struct.pack_into("<H", data, 40, 52)
    struct.pack_into("<H", data, 46, 40)
    struct.pack_into("<H", data, 48, 0)
    struct.pack_into("<H", data, 50, 0)

    return bytes(data)


def make_unsigned_pbp(path):
    prx = make_minimal_prx()

    # PARAM.SFO through SND0.AT3 are empty. DATA.PSP contains the minimal
    # PRX and DATA.PSAR is empty.
    offsets = [PBP_HEADER_SIZE] * 7
    offsets.append(PBP_HEADER_SIZE + len(prx))

    header = struct.pack(
        "<4sI8I",
        b"\x00PBP",
        0x00010000,
        *offsets,
    )

    path.write_bytes(header + prx)


def sign(signer, unsigned_pbp, output, workdir):
    subprocess.run(
        [signer, str(unsigned_pbp), str(output)],
        cwd=workdir,
        check=True,
    )


def validate_signed_pbp(path):
    data = path.read_bytes()
    if len(data) < PBP_HEADER_SIZE:
        raise AssertionError("signed PBP is shorter than its header")

    signature, version, *offsets = struct.unpack(
        "<4sI8I", data[:PBP_HEADER_SIZE]
    )

    if signature != b"\x00PBP":
        raise AssertionError("signed output has an invalid PBP signature")
    if version != 0x00010000:
        raise AssertionError("signed output changed the PBP version")
    if offsets != sorted(offsets):
        raise AssertionError("PBP section offsets are not monotonic")
    if offsets[0] != PBP_HEADER_SIZE:
        raise AssertionError("first PBP section does not start after the header")
    if offsets[6] != PBP_HEADER_SIZE:
        raise AssertionError("unexpected data before DATA.PSP")
    if offsets[7] != len(data):
        raise AssertionError("DATA.PSAR is expected to be empty")

    signed_psp = data[offsets[6]:offsets[7]]
    if len(signed_psp) != SIGNED_PSP_SIZE:
        raise AssertionError(
            "unexpected signed DATA.PSP size: "
            f"{len(signed_psp)} != {SIGNED_PSP_SIZE}"
        )
    if signed_psp[:4] != b"~PSP":
        raise AssertionError("signed DATA.PSP does not begin with ~PSP")


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: test_ebootsign.py /path/to/ebootsign")

    signer = str(pathlib.Path(sys.argv[1]).resolve())

    with tempfile.TemporaryDirectory(prefix="ebootsign-test-") as tmp:
        root = pathlib.Path(tmp)
        unsigned_pbp = root / "EBOOT.PBP"
        make_unsigned_pbp(unsigned_pbp)

        outputs = []
        for index in range(2):
            workdir = root / f"run-{index}"
            workdir.mkdir()
            output = root / f"EBOOT-signed-{index}.PBP"
            sign(signer, unsigned_pbp, output, workdir)
            validate_signed_pbp(output)
            outputs.append(output.read_bytes())

        first_hash = hashlib.sha256(outputs[0]).hexdigest()
        second_hash = hashlib.sha256(outputs[1]).hexdigest()

        if outputs[0] != outputs[1]:
            raise AssertionError(
                "signing the same EBOOT twice was not deterministic: "
                f"{first_hash} != {second_hash}"
            )

        print(f"deterministic signed EBOOT SHA-256: {first_hash}")


if __name__ == "__main__":
    main()
