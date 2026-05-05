if __name__ == "__main__":
    import requests

    yt_ids = [
        "w_N_D7sP7qI",
        "c1j6sPjHjJg",
        "wH2n2T382zQ",
        "8ZoJcHnBjgA",  # te happy/romantic
        "OARJpAHZhHo",
        "EhCmBShtMgo",
        "Lh-H-O6_rpU",
        "lE64AXVbsJ4",  # te energetic
    ]

    for yid in yt_ids:
        url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={yid}&format=json"
        r = requests.get(url)
        if r.status_code == 200:
            print(f"{yid}: OK")
        else:
            print(f"{yid}: BLOCKED")
