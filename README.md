# Shopee Flash Sale Assistant Indonesia

Aplikasi desktop Windows untuk menyiapkan sesi flash sale Shopee. Ada antarmuka GUI dan versi terminal. Aplikasi menyimpan produk lokal, menampilkan hitung mundur WIB, menyediakan konfigurasi jumlah/varian/batas harga, serta menjalankan otomatisasi browser Chrome pada jadwal atau saat tombol Mulai bot diklik.

**Bukan jaminan memenangkan flash sale.** Aplikasi ini tidak melewati CAPTCHA, antrean, batas pembelian, rate limit, atau perlindungan akun. Bot mencoba memilih varian yang dikonfigurasi dan membuka alur Beli Sekarang jika tombol dapat dikenali. Pesanan akhir dan pembayaran tidak dikirim otomatis; verifikasi yang diminta Shopee ditangani pengguna.

## Aplikasi desktop (disarankan)
1. Download ZIP dari tombol **Code → Download ZIP** di GitHub lalu ekstrak.
2. Cara tanpa instalasi Python: buka tab **Actions** di GitHub, pilih workflow **Build Windows desktop app**, buka run yang berhasil, lalu unduh artifact `ShopeeFlashSale-Windows`. Ekstrak ZIP dan jalankan `ShopeeFlashSale.exe`.
3. Alternatif menjalankan source code: pasang Python 3.10+ dan Google Chrome, lalu jalankan `py -m pip install -r requirements.txt`. Klik dua kali `Jalankan-Aplikasi.bat` atau jalankan:
   ```powershell
   py -3 app.py
   ```
4. Isi nama produk, URL HTTPS Shopee, dan jadwal WIB dalam format `YYYY-MM-DD HH:MM`.
5. Klik **Tambah produk**, pilih produk dari daftar, tekan **Konfigurasi bot** untuk jumlah, nama varian persis, dan batas harga maksimum.
6. Klik **Aktifkan jadwal**. Pada waktu yang ditentukan, aplikasi membuka Chrome dengan profil khusus lokal dan mencoba melanjutkan alur pembelian. Tombol **Mulai bot** menjalankan alur langsung untuk produk terpilih.
7. Pada penggunaan pertama, login sendiri ke Shopee di jendela Chrome yang dibuka. Jika login/verifikasi diperlukan, selesaikan secara manual lalu jalankan bot kembali. Jangan masukkan kredensial di aplikasi ini.

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
- GUI memakai Tkinter; otomatisasi browser memakai Playwright dan Google Chrome yang terpasang di komputer.
- Data produk disimpan di `data/products.json` di komputer pengguna.
- Jangan menyimpan password, cookie, token sesi, atau data pembayaran di repository.
- Aplikasi tidak menyelesaikan CAPTCHA, menerobos antrean, atau mengirim pesanan/pembayaran final. Jika pemilihan varian atau tombol tidak dapat dikenali, pengguna perlu memeriksa halaman Chrome.
- Keberhasilan tetap dipengaruhi stok, latensi jaringan, browser, dan sistem Shopee.
