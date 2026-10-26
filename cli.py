"""Command-line interface.

  python cli.py embed   cover.png  out.png  "secret text"  [-p PASSWORD]
  python cli.py extract out.png  [-p PASSWORD]
"""
import argparse
import sys

import stego


def main():
    ap = argparse.ArgumentParser(description="LSB image steganography")
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("embed"); e.add_argument("cover"); e.add_argument("output")
    e.add_argument("message"); e.add_argument("-p", "--password", default="")
    x = sub.add_parser("extract"); x.add_argument("image")
    x.add_argument("-p", "--password", default="")
    a = ap.parse_args()
    try:
        if a.cmd == "embed":
            cover = stego.load_rgb(a.cover)
            out = stego.embed(cover, a.message, a.password)
            stego.save_png(out, a.output)
            q = stego.quality(cover, out)
            print(f"Saved {a.output}  |  MSE {q['mse']:.5f}  |  PSNR {q['psnr']:.2f} dB")
        else:
            print(stego.extract(stego.load_rgb(a.image), a.password))
    except stego.StegoError as err:
        sys.exit(f"Error: {err}")


if __name__ == "__main__":
    main()
