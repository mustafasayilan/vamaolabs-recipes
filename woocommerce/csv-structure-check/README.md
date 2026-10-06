# Check CSV structure before a WooCommerce import

An independent, read-only Python example by Mustafa Sayilan / VamaoLabs. It checks file structure before you touch a store. It does not connect to WordPress or replace WooCommerce's importer.

## Requirements and use

Python 3.13, standard library only. No installation, API key, account or network access required. Keep the original CSV and run against a copy:

```text
python check_csv.py products.csv
```

Output is JSON. `ok` exits 0; `review` or `error` exits 1. Issues contain line numbers and codes, not product values. A quoted multiline field reports the physical line where its record ends. Empty physical lines are ignored. A one-column file is flagged for delimiter review, even if intentionally one-column.

Checks: UTF-8 (BOM accepted), missing/empty/repeated headers (trimmed and case-insensitive), comma-separated row width, malformed quoting and null bytes. Reads at most 10 MiB plus one byte and reports at most 100 issues plus a limit marker. This protects a local diagnostic run from unexpectedly large supplier files; it is not WooCommerce's upload limit.

It does NOT validate product IDs, SKU uniqueness, existing catalog matches, variation links, prices, inventory, images, custom fields or import behavior. `ok` means only these structure checks found no issue. Column mapping and a staging import are still necessary. Back up before any real import.

## Local verification

```text
python -m unittest -v
docker run --rm --network none --read-only --cap-drop ALL --security-opt no-new-privileges --tmpfs /tmp -v "YOUR_RECIPE_FOLDER:/work:ro" -w /work python:3.13-alpine python -B -m unittest -v
```

The tests cover quoted commas, multiline fields, Unicode/BOM, malformed encoding, headers, delimiter review, too many/few cells, bad quotes, null bytes, size/issue bounds, missing files, exit codes and unchanged source files. Verified locally in Python 3.13 Docker; this is a standalone CSV check, NOT a claim that a particular WooCommerce release was end-to-end tested by this recipe.

## Source and license

[WooCommerce's official importer guide](https://woocommerce.com/document/product-csv-importer-exporter/) explains its UTF-8 CSV and mapping workflow. The code here is original independent Python, not copied from WooCommerce or a paid VamaoLabs product. MIT; see LICENSE. Platform-derived future examples must carry their own appropriate license.

[VamaoLabs technical guides](https://vamaolabs.com/blog) explain practical checks and their limitations. I build VamaoLabs products; product recommendations disclose that affiliation.
