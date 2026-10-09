#!/usr/bin/env python3
"""Shopee Indonesia flash-sale preparation helper. Standard library only."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import webbrowser
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

APP_DIR = Path(__file__).resolve().parent
DATA_FILE = APP_DIR / "data" / "products.json"
WIB = timezone(timedelta(hours=7), name="WIB")


def now_wib() -> datetime:
    return datetime.now(WIB)


def parse_sale_time(value: str) -> datetime:
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d %H:%M")
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "Format waktu harus YYYY-MM-DD HH:MM, contoh: 2026-10-10 12:00"
        ) from exc
    return parsed.replace(tzinfo=WIB)


def validate_shopee_url(value: str) -> str:
    parsed = urlparse(value.strip())
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not (
        host == "shopee.co.id" or host.endswith(".shopee.co.id")
        or host == "shopee.com" or host.endswith(".shopee.com")
    ):
        raise argparse.ArgumentTypeError(
            "Masukkan tautan HTTPS produk dari shopee.co.id atau shopee.com."
        )
    return value.strip()


def load_products() -> list[dict]:
    if not DATA_FILE.exists():
        return []
    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("Format data bukan daftar.")
        return data
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: Tidak bisa membaca {DATA_FILE}: {exc}", file=sys.stderr)
        raise SystemExit(2)


def save_products(products: list[dict]) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary = DATA_FILE.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(products, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(DATA_FILE)


def get_product(products: list[dict], product_id: int) -> dict:
    for product in products:
        if product.get("id") == product_id:
            return product
    raise SystemExit(f"Produk ID {product_id} tidak ditemukan. Jalankan: py main.py list")


def format_remaining(target: datetime) -> str:
    seconds = int((target - now_wib()).total_seconds())
    if seconds <= 0:
        return "sudah waktunya"
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    prefix = f"{days}h " if days else ""
    return f"{prefix}{hours:02}:{minutes:02}:{seconds:02}"


def alert(message: str) -> None:
    print("\n" + "=" * 64)
    print("\a" + message)
    print("=" * 64, flush=True)
    if os.name == "nt":
        try:
            import winsound
            for _ in range(3):
                winsound.Beep(1200, 250)
                time.sleep(0.1)
        except (ImportError, RuntimeError):
            pass


def cmd_add(args: argparse.Namespace) -> None:
    products = load_products()
    next_id = max((int(p.get("id", 0)) for p in products), default=0) + 1
    sale_at = parse_sale_time(args.sale_at)
    product = {
        "id": next_id,
        "name": args.name.strip(),
        "url": validate_shopee_url(args.url),
        "sale_at": sale_at.isoformat(),
        "opened": False,
    }
    if not product["name"]:
        raise SystemExit("Nama produk tidak boleh kosong.")
    products.append(product)
    save_products(products)
    print(f"Produk disimpan (ID {next_id}): {product['name']}")
    print(f"Waktu sale: {sale_at:%Y-%m-%d %H:%M:%S WIB}")
    print("Jalankan 'py main.py run' dan biarkan terminal tetap terbuka.")


def cmd_list(_: argparse.Namespace) -> None:
    products = load_products()
    if not products:
        print("Belum ada produk. Tambahkan dengan: py main.py add --help")
        return
    print(f"{'ID':<4} {'STATUS':<12} {'HITUNG MUNDUR':<18} {'PRODUK'}")
    print("-" * 76)
    for p in sorted(products, key=lambda x: x.get("sale_at", "")):
        target = datetime.fromisoformat(p["sale_at"]).astimezone(WIB)
        if p.get("opened"):
            status = "sudah dibuka"
        elif target <= now_wib():
            status = "siap dibuka"
        else:
            status = "menunggu"
        print(f"{p['id']:<4} {status:<12} {format_remaining(target):<18} {p['name']}")
        print(f"     {target:%Y-%m-%d %H:%M WIB} | {p['url']}")


def cmd_open(args: argparse.Namespace) -> None:
    product = get_product(load_products(), args.id)
    print(f"Membuka: {product['name']}")
    if not webbrowser.open(product["url"], new=2):
        print("Browser tidak dapat dibuka otomatis. Salin tautan ini:")
        print(product["url"])
    else:
        print("Halaman produk dikirim ke browser default.")
    print("Lanjutkan pembelian secara manual dan ikuti semua pemeriksaan Shopee.")


def cmd_remove(args: argparse.Namespace) -> None:
    products = load_products()
    get_product(products, args.id)
    products = [p for p in products if p.get("id") != args.id]
    save_products(products)
    print(f"Produk ID {args.id} dihapus.")


def cmd_run(_: argparse.Namespace) -> None:
    products = load_products()
    if not products:
        raise SystemExit("Belum ada produk. Tambahkan produk dahulu dengan perintah add.")
    pending = {p["id"]: p for p in products if not p.get("opened")}
    if not pending:
        print("Semua produk sudah ditandai dibuka. Tambah produk baru atau reset opened di data/products.json.")
        return

    print("Shopee Flash Sale Assistant aktif (WIB). Tekan Ctrl+C untuk berhenti.")
    print("Bot hanya membuka halaman dan memberi peringatan; checkout tetap manual.")
    try:
        while pending:
            current = now_wib()
            due = []
            next_target = None
            for product in pending.values():
                target = datetime.fromisoformat(product["sale_at"]).astimezone(WIB)
                if target <= current:
                    due.append(product)
                elif next_target is None or target < next_target:
                    next_target = target

            for product in due:
                alert(f"SALE TIME: {product['name']} (ID {product['id']})")
                opened = webbrowser.open(product["url"], new=2)
                if not opened:
                    print(f"Browser gagal dibuka. Buka manual: {product['url']}")
                else:
                    print(f"Halaman dibuka: {product['url']}")
                product["opened"] = True
                pending.pop(product["id"], None)
                save_products(load_products_with_updates(product))
                print("Selesaikan checkout sendiri; jangan abaikan CAPTCHA atau antrean Shopee.")

            if not pending:
                break

            nearest = min(
                datetime.fromisoformat(p["sale_at"]).astimezone(WIB)
                for p in pending.values()
            )
            remaining = max(0, int((nearest - now_wib()).total_seconds()))
            print(
                f"\rBerikutnya dalam {format_remaining(nearest)} | "
                f"{len(pending)} produk menunggu. Ctrl+C untuk berhenti.",
                end="", flush=True,
            )
            time.sleep(0.2 if remaining <= 2 else 1)
    except KeyboardInterrupt:
        print("\nScheduler dihentikan. Produk yang belum waktunya tetap tersimpan.")
    print("\nSelesai.")


def load_products_with_updates(updated: dict) -> list[dict]:
    products = load_products()
    for item in products:
        if item.get("id") == updated["id"]:
            item.update(updated)
            break
    return products


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Shopee Indonesia Flash Sale Assistant — persiapan cepat, checkout manual."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="Simpan tautan produk dan jadwal sale (WIB).")
    add.add_argument("--name", required=True, help="Nama singkat produk.")
    add.add_argument("--url", required=True, type=validate_shopee_url, help="URL produk Shopee HTTPS.")
    add.add_argument("--sale-at", required=True, help="Waktu WIB: YYYY-MM-DD HH:MM.")
    add.set_defaults(func=cmd_add)

    listing = sub.add_parser("list", help="Tampilkan produk dan hitung mundur.")
    listing.set_defaults(func=cmd_list)

    opening = sub.add_parser("open", help="Buka produk di browser sekarang.")
    opening.add_argument("id", type=int, help="ID dari perintah list.")
    opening.set_defaults(func=cmd_open)

    remove = sub.add_parser("remove", help="Hapus produk tersimpan.")
    remove.add_argument("id", type=int, help="ID dari perintah list.")
    remove.set_defaults(func=cmd_remove)

    run = sub.add_parser("run", help="Tunggu jadwal lalu buka halaman produk.")
    run.set_defaults(func=cmd_run)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except (argparse.ArgumentTypeError, OSError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
