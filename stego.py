"""Core LSB steganography engine (no UI code here).

Payload layout (hidden in the least significant bit of every R, G, B value,
row by row, left to right; bits are written MSB first):

    "STG1" (4 bytes) | flag (1 byte: 0 plain, 1 AES) | length (4 bytes, big-endian)
    | body  (plain UTF-8 text, or salt[16] + nonce[12] + AES-GCM ciphertext)

This is byte-compatible with the browser version, so images can be
hidden in one and extracted in the other.
"""
import os
import struct

import numpy as np
from PIL import Image
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

MAGIC = b"STG1"
HEADER_BYTES = 9


class StegoError(Exception):
    """Raised for any user-facing failure (too big, wrong password, ...)."""


def _derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100_000)
    return kdf.derive(password.encode("utf-8"))


def load_rgb(source) -> np.ndarray:
    """Open an image (path or file-like) as an RGB uint8 array (h, w, 3).
    Transparent pixels are flattened onto white so no bits are lost."""
    img = Image.open(source)
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
        bg.alpha_composite(img)
        img = bg
    return np.array(img.convert("RGB"), dtype=np.uint8)


def capacity(arr: np.ndarray) -> int:
    """Maximum body size in bytes that fits in this image."""
    return arr.size // 8 - HEADER_BYTES


def embed(arr: np.ndarray, message: str, password: str = "") -> np.ndarray:
    """Return a new stego array with `message` hidden (optionally AES-encrypted)."""
    body = message.encode("utf-8")
    flag = 0
    if password:
        salt, nonce = os.urandom(16), os.urandom(12)
        body = salt + nonce + AESGCM(_derive_key(password, salt)).encrypt(nonce, body, None)
        flag = 1
    if len(body) > capacity(arr):
        raise StegoError(
            f"Message too large: need {len(body)} bytes, image holds {capacity(arr)}."
        )
    payload = MAGIC + struct.pack(">BI", flag, len(body)) + body
    bits = np.unpackbits(np.frombuffer(payload, dtype=np.uint8))  # binary encoding
    flat = arr.flatten()  # flatten() returns a copy, original stays untouched
    flat[: bits.size] = (flat[: bits.size] & 0xFE) | bits
    return flat.reshape(arr.shape)


def _read_bytes(flat: np.ndarray, start_byte: int, n: int) -> bytes:
    bits = flat[start_byte * 8 : (start_byte + n) * 8] & 1
    return np.packbits(bits).tobytes()


def extract(arr: np.ndarray, password: str = "") -> str:
    """Recover the hidden message or raise StegoError."""
    flat = arr.flatten()
    if flat.size < HEADER_BYTES * 8:
        raise StegoError("Image is too small to contain hidden data.")
    header = _read_bytes(flat, 0, HEADER_BYTES)
    if header[:4] != MAGIC:
        raise StegoError("No hidden data found (or the image was edited/compressed).")
    flag, length = struct.unpack(">BI", header[4:9])
    if length > capacity(arr):
        raise StegoError("Corrupted header - the image was probably modified.")
    body = _read_bytes(flat, HEADER_BYTES, length)
    if flag == 1:
        if not password:
            raise StegoError("This message is password-protected. Enter the password.")
        try:
            plain = AESGCM(_derive_key(password, body[:16])).decrypt(body[16:28], body[28:], None)
        except Exception:
            raise StegoError("Wrong password or corrupted data.")
        return plain.decode("utf-8")
    return body.decode("utf-8")


def quality(original: np.ndarray, stego: np.ndarray) -> dict:
    """MSE and PSNR between cover and stego image."""
    diff = original.astype(np.float64) - stego.astype(np.float64)
    mse = float(np.mean(diff ** 2))
    psnr = float("inf") if mse == 0 else 10 * np.log10(255.0 ** 2 / mse)
    changed = int(np.count_nonzero(original != stego))
    return {"mse": mse, "psnr": psnr, "changed_values": changed}


def save_png(arr: np.ndarray, path) -> None:
    Image.fromarray(arr).save(path, format="PNG")
