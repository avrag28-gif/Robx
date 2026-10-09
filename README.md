# Shopee Flash Sale Assistant (Indonesia)

CLI helper for Windows that prepares a Shopee Indonesia flash-sale session. It stores product links locally, shows countdowns, opens the selected product page at the configured time, and alerts in the terminal.

**No purchase or sale win is guaranteed.** The app does not bypass CAPTCHA, queues, rate limits, account controls, purchase limits, or checkout protections. Checkout and confirmations remain manual in Shopee's official page/app.

## Requirements
- Windows 10/11
- Python 3.10+ (standard library only)

## Quick start
1. Open PowerShell in the downloaded/cloned project directory.
2. Save a product and its sale time (WIB, UTC+7):
   ```powershell
   py main.py add --name "Nama produk" --url "https://shopee.co.id/..." --sale-at "2026-10-10 12:00"
   ```
3. View saved products and countdowns: `py main.py list`
4. Keep the terminal running until the sale: `py main.py run`
5. Open a product immediately: `py main.py open 1`
6. Remove a product: `py main.py remove 1`

Use `py main.py --help` for commands. The scheduler opens the product page and alerts at the selected time; complete checkout yourself.

## Prepare ahead
- Sign in through the official Shopee app/site before the sale.
- Verify delivery address, payment method, product variant, seller, total price and purchase limits.
- Keep your device clock synchronized and use a stable connection.
- Do not run multiple sessions or tools that may trigger account protections.

## Privacy and limitations
Product names, URLs and sale times are stored locally in `data/products.json`. The app does not ask for or store passwords, cookies or payment data. It is not an official Shopee integration and does not scrape private endpoints or automate checkout. Browser/network latency and Shopee's stock, queues and controls remain outside its control.
