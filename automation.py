"""Shopee browser automation helper using the user's own Chrome session."""
from __future__ import annotations

import re
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

ROOT = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
PROFILE_DIR = ROOT / "data" / "chrome-profile"


def run_product_flow(url: str, quantity: int = 1, variant: str = "",
                     max_price: int = 0, callback=None):
    """Open product, optionally select an exact visible variant, and advance to checkout.

    It deliberately does not submit the final order or payment, solve CAPTCHA,
    bypass queues, or circumvent purchase limits.
    """
    def log(message):
        if callback:
            callback(message)

    if quantity < 1 or quantity > 99:
        raise ValueError("Jumlah harus antara 1 dan 99.")
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    log("Membuka Chrome dengan profil lokal khusus aplikasi…")
    with sync_playwright() as p:
        try:
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(PROFILE_DIR), channel="chrome",
                headless=False, viewport={"width": 1365, "height": 900},
                args=["--start-maximized"],
            )
        except Exception as exc:
            raise RuntimeError(
                "Google Chrome belum terpasang atau Playwright belum terinstal. "
                "Jalankan: py -m pip install -r requirements.txt. "
                f"Detail: {exc}"
            ) from exc
        page = context.pages[0] if context.pages else context.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(2000)
            body = page.locator("body").inner_text(timeout=5000)
            if re.search(r"captcha|robot check|verifikasi keamanan", body, re.I):
                log("Shopee meminta verifikasi. Selesaikan sendiri di Chrome; bot tidak melewatinya.")
                page.wait_for_event("close", timeout=3600000)
                return {"status": "user_verification", "message": "Verifikasi ditangani pengguna."}
            if re.search(r"masuk|log in|login", page.title(), re.I) and "shopee" in page.url.lower():
                log("Periksa login di Chrome. Login hanya dilakukan langsung oleh pengguna.")
                page.wait_for_event("close", timeout=3600000)
                return {"status": "login_check", "message": "Periksa sesi login."}

            if variant:
                log(f"Mencari varian dengan nama persis: {variant}")
                try:
                    choice = page.get_by_text(variant, exact=True).first
                    choice.wait_for(state="visible", timeout=5000)
                    choice.click(timeout=3000)
                except PlaywrightTimeoutError:
                    log("Varian tidak ditemukan dengan pasti. Pilih varian yang benar secara manual.")
                    page.wait_for_event("close", timeout=3600000)
                    return {"status": "variant_manual", "message": "Pemilihan varian perlu diperiksa."}

            if quantity > 1:
                log(f"Mencoba mengatur jumlah menjadi {quantity}…")
                # Only click a visible increment control; never type into an unknown field.
                plus = page.get_by_role("button", name=re.compile(r"^(\+|Tambah|Increase)$", re.I))
                try:
                    for _ in range(quantity - 1):
                        plus.first.click(timeout=1000)
                        page.wait_for_timeout(100)
                except Exception:
                    log("Kontrol jumlah tidak dikenali; atur jumlah secara manual sebelum membeli.")

            buy = page.get_by_text(re.compile(r"^(Beli Sekarang|Buy Now)$", re.I)).first
            try:
                buy.wait_for(state="visible", timeout=8000)
            except PlaywrightTimeoutError:
                log("Tombol Beli Sekarang tidak ditemukan. Periksa halaman dan pilih varian secara manual.")
                page.wait_for_event("close", timeout=3600000)
                return {"status": "manual", "message": "Tombol beli tidak ditemukan."}

            if max_price > 0:
                log(f"Batas harga disetel Rp{max_price:,}; angka halaman akan diperiksa setelah checkout terbuka.")
            buy.click(timeout=5000)
            page.wait_for_timeout(2500)

            if max_price > 0:
                body = page.locator("body").inner_text(timeout=5000)
                # Conservative guard: if the configured ceiling is exceeded by a clearly
                # visible rupiah amount, stop and leave the page open for inspection.
                visible_prices = [
                    int(v.replace(".", "").replace(",", ""))
                    for v in re.findall(r"Rp\s*([0-9][0-9.,]{3,})", body)
                ]
                if visible_prices and max(visible_prices) > max_price:
                    log("Harga yang terbaca melampaui batas. Jangan lanjutkan; periksa harga/total secara manual.")
                    page.wait_for_event("close", timeout=3600000)
                    return {"status": "price_guard", "message": "Pemeriksaan batas harga meminta pemeriksaan manual."}

            log("Halaman checkout dibuka jika alur Shopee mengizinkan. Periksa varian, alamat, ongkir, dan total; bot tidak mengirim pesanan atau pembayaran.")
            # Keep the browser available for the user to review and complete the order.
            try:
                page.wait_for_event("close", timeout=3600000)
            except PlaywrightTimeoutError:
                log("Jendela Chrome masih terbuka. Tutup Chrome setelah selesai.")
            return {"status": "checkout_open", "message": "Browser dibiarkan terbuka untuk pemeriksaan pengguna."}
        finally:
            try:
                context.close()
            except Exception:
                pass
