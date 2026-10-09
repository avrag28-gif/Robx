"""Shopee browser automation helper.

Uses the user's own Chrome session. It does not solve CAPTCHA, evade queues,
or submit the final order/payment; it can open the product and advance through
visible product-page actions when the page permits it.
"""
from __future__ import annotations

import os
import re
import threading
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

ROOT = Path(__file__).resolve().parent
PROFILE_DIR = ROOT / "data" / "chrome-profile"
_log_lock = threading.Lock()


def _log(callback, message):
    if callback:
        with _log_lock:
            callback(message)


def run_product_flow(url: str, quantity: int = 1, variant: str = "",
                     max_price: int = 0, callback=None):
    """Open Shopee in a persistent browser session and advance to checkout."""
    if quantity < 1 or quantity > 99:
        raise ValueError("Jumlah harus antara 1 dan 99.")
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    _log(callback, "Membuka Chrome dengan sesi lokal yang tersimpan…")
    with sync_playwright() as p:
        try:
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(PROFILE_DIR),
                channel="chrome",
                headless=False,
                viewport={"width": 1365, "height": 900},
                args=["--start-maximized"],
            )
        except Exception as exc:
            raise RuntimeError(
                "Chrome tidak ditemukan atau gagal dijalankan. Pasang Google Chrome "
                "dan dependensi Playwright (pip install -r requirements.txt). "
                f"Detail: {exc}"
            ) from exc
        try:
            page = context.pages[0] if context.pages else context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(2500)
            if "login" in page.url.lower() or any(x in page.url.lower() for x in ("captcha", "verify")):
                _log(callback, "Login/verifikasi diperlukan. Selesaikan sendiri di jendela Chrome; lalu jalankan lagi.")
                return {"status": "needs_user", "message": "Login atau verifikasi diperlukan."}

            # Product variants are intentionally user-selected in the browser to avoid
            # choosing the wrong SKU based on ambiguous text.
            if variant:
                _log(callback, f"Varian diminta: {variant}. Periksa/pilih varian itu di halaman produk sebelum lanjut.")
            _log(callback, "Mencari tombol Beli Sekarang / Buy Now…")
            buy = page.get_by_text(re.compile(r"^(Beli Sekarang|Buy Now)$", re.I)).first
            try:
                buy.wait_for(state="visible", timeout=8000)
            except PlaywrightTimeoutError:
                _log(callback, "Tombol beli tidak ditemukan. Pilih varian atau selesaikan verifikasi di Chrome, lalu klik tombolnya sendiri.")
                return {"status": "needs_user", "message": "Tombol beli tidak ditemukan."}

            # If variant modal appears, do not guess SKU selection.
            page.wait_for_timeout(500)
            modal_text = ""
            try:
                modal_text = page.locator("body").inner_text(timeout=1500)
            except Exception:
                pass
            if variant and variant.lower() not in modal_text.lower():
                _log(callback, "Pastikan varian yang benar dipilih di halaman. Bot tidak akan menebak SKU.")
                return {"status": "needs_user", "message": "Perlu pemilihan varian manual."}

            # Adjust quantity only where a clear quantity control exists.
            if quantity > 1:
                plus = page.get_by_role("button", name=re.compile(r"^(\+|Tambah|Increase)$", re.I))
                try:
                    for _ in range(quantity - 1):
                        awaitable = plus.first.click(timeout=1000)
                        page.wait_for_timeout(120)
                except Exception:
                    _log(callback, "Kontrol jumlah tidak dikenali; periksa jumlah langsung di halaman.")

            # Click Buy Now only; do not submit place-order/payment actions.
            buy.click(timeout=5000)
            page.wait_for_timeout(2500)
            if max_price > 0:
                body = page.locator("body").inner_text(timeout=5000)
                prices = [int(v.replace(".", "").replace(",", "")) for v in re.findall(r"(?:Rp\s*)?([0-9][0-9.,]{3,})", body)]
                if prices and min(prices) > max_price:
                    _log(callback, f"Harga terbaca di halaman melebihi batas Rp{max_price:,}. Hentikan dan periksa total.")
                    return {"status": "price_check", "message": "Harga melewati batas yang ditetapkan."}
            _log(callback, "Aksi Beli Sekarang dijalankan. Periksa varian, alamat, ongkir, total, dan lanjutkan sendiri di checkout.")
            # Keep browser open so the user can inspect and finish the order.
            return {"status": "checkout_open", "message": "Checkout dibuka; pesanan/pembayaran belum dikirim."}
        finally:
            # Keep persistent browser open for user interaction.
            pass
