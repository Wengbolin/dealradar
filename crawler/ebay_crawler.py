import requests

ACCESS_TOKEN = "v^1.1#i^1#r^0#I^3#f^0#p^1#t^H4sIAAAAAAAA/+VYb2xTVRRftw4zNyAwZGQRLI8ZE+C19722r+0LLXQbSAf741qKzD/4+t5929vev737SlsSQjOVAB/E8AWjxmEUlA9EjAbxD0YQPrBgCAFN1Bg1QoIGQxiigUjifW0Z3SQMWY1L7Jfm3Xvuuef3O+fcc+4F2SlVC7es3PLHVNt95buzIFtus1HVoGpK5aJpFeX1lWWgSMC2O9uQtQ9UXFiCOEXW2U6IdE1F0JFWZBWxucEgkTRUVuOQhFiVUyBiTZ6NhltXs7QTsLqhmRqvyYQj0hwkONEn8l4Pw0DgAxwv4FH1ps6YFiR8PhqKAa/gp72M2x8Q8TxCSRhRkcmpZpCgAc2QwE0CJkYFWBqwNO10++guwhGHBpI0FYs4ARHKmcvm1hpFtt7ZVA4haJhYCRGKhFdE28OR5uVtsSWuIl2hAg9RkzOTaPRXkyZAR5yTk/DO26CcNBtN8jxEiHCF8juMVsqGbxpzD+bnqPb4/AGKcSdo4OMF3u8vCZUrNEPhzDvbYY1IAinmRFmompKZGY9RzEaiF/Jm4asNq4g0O6y/x5KcLIkSNILE8sbwunBHBxFKaLKkpqBKNkNO7uQEjuzobCb9CdHnCdBigvT4AoIvADyFjfLaCjSP2alJUwXJIg052jSzEWKr4VhuqCJusFC72m6ERdOyqEiOpm5y6AVdllPzXkyaParlV6hgIhy5z/E9MLLaNA0pkTThiIaxEzmKcFrpuiQQYydzsVgInzQKEj2mqbMuVyqVcqbcTs3odtEAUK7HW1dH+R6ocASWtXI9Ly+Nv4CUclB4iFciiTUzOrYljWMVG6B2EyEvQ3s8dIH30WaFxo7+baAIs2t0RpQqQ5iETwCCH/oofwIwUChFhoQKQeqy7IAJLkMqnNEHTV3meEjyOM6SCjQkgXV7RdrtFyEpMAGR9AREkUx4BYakRAgBhIkEH/D/nxLlbkM9CnkDmiWJ9ZLFeVuiMRaXPKnllB7pF2IdqRaUZJSNKpNeEwus5DLx3iZPa69/Dc6G4N1mw23BN8kSZiaG9y8FAVaul46ElRoyoTAheFFe02EHjlk+M7kc7DaEDs4wM1Eo44TqnhDIsK5HSnNWlwzePzwm7g136WrUf1SfbosKWSE7uVBZ6xFWwOmS06pATl5TXFauaxxuP6zh9TmrJ4Rbwp3rpEKNQebRSkK+5XTm4DrRBt5pQKQlDdxtO9utDiym9UEV1zPT0GQZGnFqwvmsKEmTS8hwsiV2CQJc4iZZsaXwHdFPe/z0xHDxuVK6frIdSaU4iu0Dtvnj4u/E+pXJhV03NCHJWz3mv3BlcI1+wAiV5X7UgO0oGLB9Wm6zgSXgYWoBmD+lYo29oqYeSSZ0SpzoRFK3iu/lBnT2wYzOSUZ5bdnQl1+3zfu45e1t5+qyzze4dpZNK3o/2f0UmDPyglJVQVUXPaeAB2/NVFLT66bSDHADhgrgBpnuAgtuzdqp2fZZdRttj1wYVJpubHqyevDd1TuOnNJlMHVEyGarLMPOLqPn7ao3iJmB9+8/1nCGOrvi4NWFqxbdeLWqbjufIl9ZLJzeP7/2hdoPtvfZXwJq9YnN7TN6jK4TXe98foB/Y/NG+sBz6978fkf68PDx+LWl9vNg2Yu9DfsGjGeHdrW3pOufufpnlRApuz484P1qkzG87Yx8rkafccU169Bs8Kv7bM3QkX5lz+X9l+Z+Eaw58t3RwdDOvbv6L72cPonW/vDao+8t+mTO9Zb4vunBmXPPHx8yeqJD9geu9F8+VnuamZF6aEG0/RtY6W9ctYHas3ZpzXDVyY86LzZmZx1cHPgle26r4/dT1T9eG/g5Uzl4cO/Wi2tr5rz+2+FlmQ3zOHD4p7e+PWS0PP1h62dP5H35F0P8RyrZEgAA', 'expires_in': 7200, 'token_type': 'Application Access Token"


def fetch_ebay():

    url = "https://api.ebay.com/buy/browse/v1/item_summary/search"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_IT"
    }

    params = {
        "q": "iphone",
        "limit": 50,
        "filter": "conditionIds:{3000},itemLocationCountry:IT",
        "sort": "newlyListed"
    }

    r = requests.get(url, headers=headers, params=params)

    data = r.json()

    ads = []

    for item in data.get("itemSummaries", []):

        try:

            ads.append({
                "id": item["itemId"],
                "title": item["title"],
                "price": float(item["price"]["value"]),
                "url": item["itemWebUrl"],
                "source": "ebay"
            })

        except:
            continue

    return ads
