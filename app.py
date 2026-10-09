#!/usr/bin/env python3
"""Shopee Flash Sale Assistant desktop GUI (Tkinter, standard library only)."""
from __future__ import annotations

import json
import os
import sys
import time
import threading
import tkinter as tk
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk
from urllib.parse import urlparse
import webbrowser

ROOT = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
DATA_FILE = ROOT / "data" / "products.json"
WIB = timezone(timedelta(hours=7), name="WIB")
BG = "#10151f"
PANEL = "#192231"
TEXT = "#eef3fb"
MUTED = "#a8b5c8"
ACCENT = "#ff6b35"
GREEN = "#4ade80"


def now_wib():
    return datetime.now(WIB)


def parse_sale_time(value: str) -> datetime:
    return datetime.strptime(value.strip(), "%Y-%m-%d %H:%M").replace(tzinfo=WIB)


def validate_url(value: str) -> str:
    parsed = urlparse(value.strip())
    host = (parsed.hostname or "").lower()
    valid_host = host in {"shopee.co.id", "shopee.com"} or host.endswith(
        (".shopee.co.id", ".shopee.com")
    )
    if parsed.scheme != "https" or not valid_host:
        raise ValueError("Gunakan tautan HTTPS resmi dari shopee.co.id atau shopee.com.")
    return value.strip()


def load_products():
    if not DATA_FILE.exists():
        return []
    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("Format data tidak valid.")
        return data
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise RuntimeError(f"Gagal membaca data produk: {exc}") from exc


def save_products(products):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = DATA_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(products, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(DATA_FILE)


def fmt_remaining(target):
    seconds = int((target - now_wib()).total_seconds())
    if seconds <= 0:
        return "WAKTUNYA!"
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return (f"{days}h " if days else "") + f"{hours:02}:{minutes:02}:{seconds:02}"


class FlashSaleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Shopee Flash Sale Assistant")
        self.root.geometry("1000x690")
        self.root.minsize(850, 600)
        self.root.configure(bg=BG)
        self.scheduler_on = False
        self.products = load_products()
        self._style()
        self._build()
        self.refresh()
        self.root.after(1000, self.tick)

    def _style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Treeview", background=PANEL, foreground=TEXT,
                        fieldbackground=PANEL, rowheight=30, borderwidth=0)
        style.configure("Treeview.Heading", background="#263448", foreground=TEXT,
                        font=("Segoe UI", 9, "bold"), relief="flat")
        style.map("Treeview", background=[("selected", "#314967")],
                  foreground=[("selected", "white")])
        style.configure("TCombobox", fieldbackground=PANEL)

    def _label(self, parent, text, color=TEXT, size=10, bold=False):
        return tk.Label(parent, text=text, bg=parent["bg"], fg=color,
                        font=("Segoe UI", size, "bold" if bold else "normal"))

    def _button(self, parent, text, command, primary=False):
        return tk.Button(parent, text=text, command=command,
                         bg=ACCENT if primary else "#2b394d",
                         fg="white", activebackground="#ff875d" if primary else "#3a4d66",
                         activeforeground="white", relief="flat", bd=0,
                         padx=14, pady=9, cursor="hand2",
                         font=("Segoe UI", 9, "bold"))

    def _build(self):
        header = tk.Frame(self.root, bg=BG, padx=22, pady=18)
        header.pack(fill="x")
        tk.Label(header, text="SHOPEE FLASH SALE", bg=BG, fg=TEXT,
                 font=("Segoe UI", 21, "bold")).pack(anchor="w")
        tk.Label(header, text="Assistant desktop • Jadwal WIB • Checkout resmi",
                 bg=BG, fg=MUTED, font=("Segoe UI", 10)).pack(anchor="w", pady=(3, 0))

        form = tk.Frame(self.root, bg=PANEL, padx=16, pady=14)
        form.pack(fill="x", padx=22, pady=(0, 14))
        self.name_var = tk.StringVar()
        self.url_var = tk.StringVar()
        self.time_var = tk.StringVar(value=now_wib().strftime("%Y-%m-%d %H:%M"))
        self._label(form, "NAMA PRODUK", MUTED, 8, True).grid(row=0, column=0, sticky="w")
        self._label(form, "URL PRODUK SHOPEE", MUTED, 8, True).grid(row=0, column=1, sticky="w", padx=(12, 0))
        self._label(form, "WAKTU SALE (WIB)", MUTED, 8, True).grid(row=0, column=2, sticky="w", padx=(12, 0))
        tk.Entry(form, textvariable=self.name_var, bg="#101722", fg=TEXT,
                 insertbackground=TEXT, relief="flat", font=("Segoe UI", 10)).grid(
                     row=1, column=0, sticky="ew", ipady=8, pady=(6, 0))
        tk.Entry(form, textvariable=self.url_var, bg="#101722", fg=TEXT,
                 insertbackground=TEXT, relief="flat", font=("Segoe UI", 10)).grid(
                     row=1, column=1, sticky="ew", padx=(12, 0), ipady=8, pady=(6, 0))
        tk.Entry(form, textvariable=self.time_var, bg="#101722", fg=TEXT,
                 insertbackground=TEXT, relief="flat", font=("Segoe UI", 10), width=19).grid(
                     row=1, column=2, sticky="ew", padx=(12, 0), ipady=8, pady=(6, 0))
        self._button(form, "＋ Tambah produk", self.add_product, True).grid(
            row=1, column=3, padx=(12, 0), pady=(6, 0))
        form.columnconfigure(0, weight=2)
        form.columnconfigure(1, weight=5)
        form.columnconfigure(2, weight=2)

        table_frame = tk.Frame(self.root, bg=BG)
        table_frame.pack(fill="both", expand=True, padx=22)
        columns = ("id", "status", "countdown", "sale", "name")
        self.table = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        for col, title, width in [
            ("id", "ID", 45), ("status", "STATUS", 105), ("countdown", "COUNTDOWN", 120),
            ("sale", "JADWAL WIB", 155), ("name", "PRODUK", 350)
        ]:
            self.table.heading(col, text=title)
            self.table.column(col, width=width, anchor="w")
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)
        self.table.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        actions = tk.Frame(self.root, bg=BG, padx=22, pady=14)
        actions.pack(fill="x")
        self._button(actions, "Buka produk", self.open_selected).pack(side="left", padx=(0, 8))
        self._button(actions, "Konfigurasi bot", self.configure_selected).pack(side="left", padx=(0, 8))
        self._button(actions, "Mulai bot", self.checkout_selected, True).pack(side="left", padx=(0, 8))
        self._button(actions, "Hapus", self.remove_selected).pack(side="left", padx=(0, 8))
        self.scheduler_button = self._button(actions, "▶ Aktifkan jadwal", self.toggle_scheduler)
        self.scheduler_button.pack(side="left")
        self.status_var = tk.StringVar(value="Siap. Tambahkan produk untuk mulai.")
        tk.Label(self.root, textvariable=self.status_var, bg="#0b1018", fg=MUTED,
                 anchor="w", padx=22, pady=10, font=("Segoe UI", 9)).pack(fill="x", side="bottom")
        tk.Label(self.root,
                 text="Catatan: CAPTCHA, antrean, pembayaran, dan konfirmasi tetap ditangani pengguna di Shopee.",
                 bg=BG, fg=MUTED, font=("Segoe UI", 8)).pack(anchor="w", padx=22, pady=(0, 10))

    def refresh(self):
        self.products = load_products()
        selected = self.table.selection()
        for item in self.table.get_children():
            self.table.delete(item)
        for p in sorted(self.products, key=lambda x: x.get("sale_at", "")):
            target = datetime.fromisoformat(p["sale_at"]).astimezone(WIB)
            status = "DIBUKA" if p.get("opened") else ("SIAP" if target <= now_wib() else "MENUNGGU")
            self.table.insert("", "end", iid=str(p["id"]), values=(
                p["id"], status, fmt_remaining(target), target.strftime("%d-%m-%Y %H:%M"), p["name"]
            ))
        for item in selected:
            if self.table.exists(item):
                self.table.selection_set(item)

    def tick(self):
        try:
            self.refresh()
            if self.scheduler_on:
                self.check_due()
        except Exception as exc:
            self.status_var.set(f"Kesalahan: {exc}")
        self.root.after(1000, self.tick)

    def add_product(self):
        try:
            name = self.name_var.get().strip()
            if not name:
                raise ValueError("Nama produk wajib diisi.")
            url = validate_url(self.url_var.get())
            target = parse_sale_time(self.time_var.get())
            products = load_products()
            pid = max((int(p.get("id", 0)) for p in products), default=0) + 1
            products.append({"id": pid, "name": name, "url": url,
                             "sale_at": target.isoformat(), "opened": False, "quantity": 1, "variant": "", "max_price": 0})
            save_products(products)
            self.name_var.set("")
            self.url_var.set("")
            self.status_var.set(f"Produk ID {pid} tersimpan.")
            self.refresh()
        except ValueError as exc:
            messagebox.showerror("Data tidak valid", str(exc), parent=self.root)
        except Exception as exc:
            messagebox.showerror("Gagal menyimpan", str(exc), parent=self.root)

    def selected_product(self):
        selection = self.table.selection()
        if not selection:
            messagebox.showinfo("Pilih produk", "Pilih satu produk dari daftar terlebih dahulu.", parent=self.root)
            return None
        return next((p for p in load_products() if str(p["id"]) == selection[0]), None)

    def open_selected(self):
        p = self.selected_product()
        if p:
            webbrowser.open(p["url"], new=2)
            self.status_var.set(f"Halaman produk dibuka: {p['name']}")

    def configure_selected(self):
        p = self.selected_product()
        if not p:
            return
        qty = simpledialog.askinteger('Konfigurasi bot', 'Jumlah barang (1-99):', initialvalue=int(p.get('quantity', 1)), minvalue=1, maxvalue=99, parent=self.root)
        if qty is None:
            return
        variant = simpledialog.askstring('Konfigurasi bot', 'Nama varian persis (opsional):', initialvalue=p.get('variant', ''), parent=self.root)
        if variant is None:
            return
        ceiling = simpledialog.askinteger('Konfigurasi bot', 'Batas harga maksimum rupiah (0 = nonaktif):', initialvalue=int(p.get('max_price', 0)), minvalue=0, parent=self.root)
        if ceiling is None:
            return
        products = load_products()
        for item in products:
            if item['id'] == p['id']:
                item['quantity'], item['variant'], item['max_price'] = qty, variant.strip(), ceiling
        save_products(products)
        self.status_var.set('Konfigurasi bot tersimpan untuk ' + p['name'])
        self.refresh()

    def start_automation(self, product):
        def worker():
            try:
                from automation import run_product_flow
                result = run_product_flow(product['url'], quantity=int(product.get('quantity', 1)), variant=product.get('variant', ''), max_price=int(product.get('max_price', 0)), callback=lambda msg: self.root.after(0, lambda m=msg: self.status_var.set(m)))
                msg = result.get('message', result.get('status', 'selesai'))
                self.root.after(0, lambda m=msg: self.status_var.set('Bot: ' + m))
            except Exception as exc:
                msg = str(exc)
                self.root.after(0, lambda m=msg: self.status_var.set('Bot gagal: ' + m))
                self.root.after(0, lambda m=msg: messagebox.showerror('Otomatisasi gagal', m, parent=self.root))
        threading.Thread(target=worker, daemon=True).start()

    def checkout_selected(self):
        p = self.selected_product()
        if not p:
            return
        if not messagebox.askyesno(
            "Lanjutkan ke Shopee",
            "Bot akan membuka Chrome dan mencoba Beli Sekarang. Periksa varian, alamat, ongkir, dan total harga; lakukan pembayaran serta konfirmasi sendiri. Lanjutkan?",
            parent=self.root
        ):
            return
        self.start_automation(p)
        self.status_var.set("Bot dimulai. Chrome akan terbuka; perhatikan status di bawah.")

    def remove_selected(self):
        p = self.selected_product()
        if not p:
            return
        if not messagebox.askyesno("Hapus produk", f"Hapus '{p['name']}' dari daftar?", parent=self.root):
            return
        save_products([x for x in load_products() if x["id"] != p["id"]])
        self.status_var.set(f"Produk ID {p['id']} dihapus.")
        self.refresh()

    def toggle_scheduler(self):
        self.scheduler_on = not self.scheduler_on
        self.scheduler_button.configure(text="■ Hentikan jadwal" if self.scheduler_on else "▶ Aktifkan jadwal")
        self.status_var.set("Jadwal aktif. Biarkan aplikasi tetap terbuka." if self.scheduler_on else "Jadwal dihentikan.")

    def check_due(self):
        products = load_products()
        changed = False
        for p in products:
            if p.get("opened"):
                continue
            target = datetime.fromisoformat(p["sale_at"]).astimezone(WIB)
            if target <= now_wib():
                self.status_var.set(f"WAKTU SALE: {p['name']} — memulai otomatisasi Chrome.")
                self.start_automation(p)
                p["opened"] = True
                changed = True
                self.root.bell()
                messagebox.showinfo(
                    "Waktu flash sale",
                    f"{p['name']}\n\nOtomatisasi Chrome dimulai. Periksa browser dan selesaikan verifikasi resmi jika diminta.",
                    parent=self.root
                )
        if changed:
            save_products(products)
            self.refresh()


def main():
    root = tk.Tk()
    try:
        FlashSaleApp(root)
    except Exception as exc:
        messagebox.showerror("Shopee Flash Sale Assistant", str(exc))
        root.destroy()
        return
    root.mainloop()


if __name__ == "__main__":
    main()
