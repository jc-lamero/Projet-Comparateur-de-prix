import re

def ldlc_price_to_cents(block) -> int | None:
    """
    LDLC: <div class="price"> 1 499€<sup>95</sup></div>
    On prend la partie euros + la partie centimes (sup).
    """
    # euros: "1 499€"
    euros_txt = block.css("div.price::text").re_first(r"\d[\d\s]*€")
    if not euros_txt:
        return None
    euros = int(re.sub(r"[^\d]", "", euros_txt))  # "1 499€" -> 1499

    # centimes: dans <sup>95</sup>
    cents_txt = block.css("div.price sup::text").get()
    if cents_txt and cents_txt.strip().isdigit():
        cents = int(cents_txt.strip())
    else:
        cents = 0

    return euros * 100 + cents
