# Shopee Flash Sale Assistant Indonesia

Aplikasi desktop Windows untuk menyiapkan sesi flash sale Shopee. Ada antarmuka GUI dan versi terminal. Aplikasi menyimpan produk secara lokal, menampilkan hitung mundur WIB, membuka halaman produk pada waktu yang dijadwalkan, dan memberi peringatan.

**Bukan jaminan memenangkan flash sale.** Aplikasi ini tidak melewati CAPTCHA, antrean, batas pembelian, rate limit, atau perlindungan akun. Pembayaran dan konfirmasi checkout tetap dilakukan pengguna pada Shopee resmi.

## Aplikasi desktop (disarankan)
1. Download ZIP dari tombol **Code → Download ZIP** di GitHub lalu ekstrak.
2. Cara tanpa instalasi Python: buka tab **Actions** di GitHub, pilih workflow **Build Windows desktop app**, buka run yang berhasil, lalu unduh artifact `ShopeeFlashSale-Windows`. Ekstrak ZIP dan jalankan `ShopeeFlashSale.exe`.
3. Alternatif menjalankan source code: pastikan Python 3.10+ terpasang, lalu klik dua kali `Jalankan-Aplikasi.bat` atau jalankan:
   ```powershell
   py -3 app.py
   ```
4. Isi nama produk, URL HTTPS Shopee, dan jadwal WIB dalam format `YYYY-MM-DD HH:MM`.
5. Klik **Tambah produk**, pilih produk dari daftar, lalu tekan **Aktifkan jadwal**.
6. Saat waktunya tiba, aplikasi akan memberi peringatan dan membuka halaman produk di browser. Tombol **Checkout (buka Shopee)** juga membuka halaman resmi setelah konfirmasi.

## Versi terminal
Simpan produk:
```powershell
py main.py add --name "Nama produk" --url "https://shopee.co.id/..." --sale-at "2026-10-10 12:00"
py main.py list
py main.py run
```
Bantuan: `py main.py --help`.

## Cara meningkatkan kesiapan
- Login ke Shopee melalui aplikasi/situs resmi sebelum flash sale.
- Siapkan alamat, metode pembayaran, dan varian terlebih dahulu.
- Pastikan jam perangkat sinkron dan koneksi stabil.
- Periksa harga total, ongkir, penjual, varian, serta batas pembelian sebelum konfirmasi.

## Batasan dan privasi
- GUI menggunakan Tkinter bawaan Python; tidak memerlukan dependensi pihak ketiga.
- Data produk disimpan di `data/products.json` di komputer pengguna.
- Jangan menyimpan password, cookie, token sesi, atau data pembayaran di repository.
- Aplikasi tidak memakai endpoint privat atau mengotomatisasi pengiriman pembayaran/konfirmasi order. CAPTCHA dan antrean resmi harus ditangani sebagaimana diminta Shopee.
- Keberhasilan tetap dipengaruhi stok, latensi jaringan, browser, dan sistem Shopee.
