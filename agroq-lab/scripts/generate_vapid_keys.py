from __future__ import annotations

import argparse
import base64
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate AgroQ VAPID keys for Web Push."
    )
    parser.add_argument(
        "--output",
        default=".env.notifications.local",
        help="Output environment file. Do not commit it.",
    )
    parser.add_argument(
        "--subject",
        default="mailto:reyesothon1921@gmail.com",
    )
    args = parser.parse_args()

    private_key = ec.generate_private_key(ec.SECP256R1())
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("ascii").strip()

    public_numbers = private_key.public_key().public_numbers()
    uncompressed = (
        b"\x04"
        + public_numbers.x.to_bytes(32, "big")
        + public_numbers.y.to_bytes(32, "big")
    )
    public_key = base64.urlsafe_b64encode(uncompressed).decode("ascii").rstrip("=")

    output = Path(args.output)
    private_value = private_pem.replace("\n", "\\n")
    output.write_text(
        "\n".join(
            [
                f"AGROQ_VAPID_PUBLIC_KEY={public_key}",
                f'AGROQ_VAPID_PRIVATE_KEY="{private_value}"',
                f"AGROQ_VAPID_SUBJECT={args.subject}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"Created {output.resolve()}")
    print("Keep this file private and never commit it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
