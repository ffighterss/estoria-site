"""Копирует site/ в папку публикации и убирает из HTML, CSS и JS служебные комментарии."""
import os
import re
import shutil
import sys

src, dst = sys.argv[1], sys.argv[2]
shutil.rmtree(dst, ignore_errors=True)
shutil.copytree(src, dst)


def clean(path, text):
    if path.endswith(".html"):
        text = re.sub(r"\s*<!--.*?-->", "", text, flags=re.S)
    elif path.endswith(".css"):
        text = re.sub(r"/\*.*?\*/\s*", "", text, flags=re.S)
    elif path.endswith(".js"):
        text = re.sub(r"/\*.*?\*/\s*", "", text, flags=re.S)
        text = re.sub(r"(?m)^\s*//.*\n", "", text)
    return text


for root, _, files in os.walk(dst):
    for name in files:
        if name.endswith((".html", ".css", ".js")):
            p = os.path.join(root, name)
            with open(p, encoding="utf-8") as f:
                text = f.read()
            with open(p, "w", encoding="utf-8") as f:
                f.write(clean(p, text))
