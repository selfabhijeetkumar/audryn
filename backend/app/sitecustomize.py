"""
AUDRYN Runtime Compatibility Layer
Automatically loaded by Python's 'site' module upon interpreter startup when in site-packages.
Also tracked here in backend/app/sitecustomize.py for repository version control and environment bootstrapping.

Provides a pure-Python RFC 9562 UUIDv7 implementation for 'uuid_utils' and 'uuid_utils.compat'
when the native unsigned C-extension (_uuid_utils.pyd) is blocked by Windows Application Control.
This ensures zero modifications to third-party wheels in site-packages and full reproducibility.
"""
import sys
import types
import os
import time
import uuid as _std_uuid

def _create_pure_python_uuid_utils():
    # Construct uuid_utils module
    mod = types.ModuleType("uuid_utils")
    mod.__version__ = "0.19.0-purepy"
    mod.__file__ = __file__

    mod.NIL = _std_uuid.UUID("00000000-0000-0000-0000-000000000000")
    mod.MAX = _std_uuid.UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")
    mod.NAMESPACE_DNS = _std_uuid.NAMESPACE_DNS
    mod.NAMESPACE_OID = _std_uuid.NAMESPACE_OID
    mod.NAMESPACE_URL = _std_uuid.NAMESPACE_URL
    mod.NAMESPACE_X500 = _std_uuid.NAMESPACE_X500
    mod.RESERVED_FUTURE = _std_uuid.RESERVED_FUTURE
    mod.RESERVED_MICROSOFT = _std_uuid.RESERVED_MICROSOFT
    mod.RESERVED_NCS = _std_uuid.RESERVED_NCS
    mod.RFC_4122 = _std_uuid.RFC_4122
    mod.SafeUUID = _std_uuid.SafeUUID
    mod.getnode = _std_uuid.getnode

    class UUID(_std_uuid.UUID):
        pass

    mod.UUID = UUID

    def _uuid4_int() -> int:
        return _std_uuid.uuid4().int

    def _uuid7_int(timestamp=None, nanos=None) -> int:
        if timestamp is None:
            ns = time.time_ns()
        elif nanos is not None:
            ns = int(timestamp * 1_000_000_000) + int(nanos)
        else:
            ns = int(timestamp * 1_000_000_000)
        ms = ns // 1_000_000
        rand_a = int.from_bytes(os.urandom(2), "big") & 0x0FFF
        rand_b = int.from_bytes(os.urandom(8), "big") & 0x3FFFFFFFFFFFFFFF
        val = (ms & 0xFFFFFFFFFFFF) << 80
        val |= (0x7 << 76)
        val |= (rand_a << 64)
        val |= (0x2 << 62)
        val |= rand_b
        return val

    def uuid1(node=None, clock_seq=None):
        return UUID(int=_std_uuid.uuid1(node, clock_seq).int)

    def uuid3(namespace, name):
        return UUID(int=_std_uuid.uuid3(namespace, name).int)

    def uuid4():
        return UUID(int=_uuid4_int())

    def uuid5(namespace, name):
        return UUID(int=_std_uuid.uuid5(namespace, name).int)

    def uuid6(node=None, timestamp=None):
        return UUID(int=_std_uuid.uuid1(node).int)

    def uuid7(timestamp=None, nanos=None):
        return UUID(int=_uuid7_int(timestamp, nanos))

    def uuid8(bytes_val):
        return UUID(bytes=bytes_val)

    def reseed():
        pass

    mod._uuid4_int = _uuid4_int
    mod._uuid7_int = _uuid7_int
    mod.uuid1 = uuid1
    mod.uuid3 = uuid3
    mod.uuid4 = uuid4
    mod.uuid5 = uuid5
    mod.uuid6 = uuid6
    mod.uuid7 = uuid7
    mod.uuid8 = uuid8
    mod.reseed = reseed

    # Construct uuid_utils.compat module
    compat_mod = types.ModuleType("uuid_utils.compat")
    compat_mod.uuid7 = uuid7
    compat_mod.UUID = UUID
    compat_mod.NIL = mod.NIL
    compat_mod.MAX = mod.MAX

    return mod, compat_mod

# Try importing native uuid_utils; if blocked by Windows Application Control, register pure-Python fallback
try:
    import uuid_utils
except ImportError as _e:
    if "Application Control" in str(_e) or "DLL load failed" in str(_e):
        _u_mod, _c_mod = _create_pure_python_uuid_utils()
        sys.modules["uuid_utils"] = _u_mod
        sys.modules["uuid_utils.compat"] = _c_mod
