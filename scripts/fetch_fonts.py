"""One-shot helper: download and self-host the design-system fonts as woff2."""

import os
import re

import requests

OUT = os.path.join(os.path.dirname(__file__), "..", "app", "static", "fonts")
URL = (
    "https://fonts.googleapis.com/css2"
    "?family=Schibsted+Grotesk:wght@600;700"
    "&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600"
    "&family=Spline+Sans+Mono:wght@500"
    "&display=swap"
)
UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}

FACE_TEMPLATE = """@font-face {{
  font-family: '{family}';
  font-style: normal;
  font-weight: {weight};
  font-display: swap;
  src: url('/static/fonts/{fname}') format('woff2');
}}
"""


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    css = requests.get(URL, headers=UA, timeout=20).text
    blocks = re.findall(r"/\* (\w+) \*/\s*@font-face\s*\{([^}]+)\}", css)
    faces = []
    seen = set()
    for subset, body in blocks:
        if subset != "latin":
            continue
        family = re.search(r"font-family:\s*'([^']+)'", body).group(1)
        weight = re.search(r"font-weight:\s*(\d+)", body).group(1)
        src = re.search(r"url\((https://[^)]+\.woff2)\)", body).group(1)
        if (family, weight) in seen:
            continue
        seen.add((family, weight))
        fname = family.replace(" ", "") + "-" + weight + ".woff2"
        data = requests.get(src, headers=UA, timeout=20).content
        with open(os.path.join(OUT, fname), "wb") as handle:
            handle.write(data)
        faces.append((family, weight, fname, len(data)))

    with open(os.path.join(OUT, "fonts.css"), "w", encoding="utf-8") as handle:
        for family, weight, fname, _size in faces:
            handle.write(FACE_TEMPLATE.format(family=family, weight=weight, fname=fname))

    for face in faces:
        print(*face)
    print("fonts.css written with", len(faces), "faces")


if __name__ == "__main__":
    main()
