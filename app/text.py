import re


def normalize_text(value: str) -> str:
    """Bikin teks mudah dibandingkan: lowercase, tanpa tanda baca, spasi rapi."""
    lowered = value.lower().strip()
    without_symbols = re.sub(r"[^a-z0-9\s]", " ", lowered)
    return re.sub(r"\s+", " ", without_symbols).strip()


def slugify(value: str) -> str:
    """Ubah judul node menjadi id aman untuk JSON, contoh: Obat Padi -> obat_padi."""
    normalized = normalize_text(value)
    slug = re.sub(r"\s+", "_", normalized)
    return slug or "rule"
