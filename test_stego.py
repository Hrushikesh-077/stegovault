import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import numpy as np, pytest, stego

def img(): return np.random.default_rng(1).integers(0, 256, (64, 64, 3), dtype=np.uint8)

def test_plain_roundtrip():
    a = img(); assert stego.extract(stego.embed(a, "hello ✓")) == "hello ✓"

def test_encrypted_roundtrip_and_wrong_password():
    a = img(); s = stego.embed(a, "top secret", "pw123")
    assert stego.extract(s, "pw123") == "top secret"
    with pytest.raises(stego.StegoError): stego.extract(s, "bad")
    with pytest.raises(stego.StegoError): stego.extract(s)

def test_too_large():
    with pytest.raises(stego.StegoError): stego.embed(img(), "x" * 5000)

def test_only_lsb_changes_and_psnr_high():
    a = img(); s = stego.embed(a, "x" * 300)
    assert np.max(np.abs(a.astype(int) - s.astype(int))) <= 1
    assert stego.quality(a, s)["psnr"] > 50

def test_no_data():
    with pytest.raises(stego.StegoError): stego.extract(img())
