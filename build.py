"""Build Maplee's browser distribution with a pinned Python runtime."""
from pathlib import Path
import argparse
import ast
import hashlib
import base64
import gzip
import json
import mimetypes
import shutil
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent
CDN = "https://cdn.jsdelivr.net/npm/brython@3.12.4/"
RUNTIME = {
    "brython.min.js": "6f96a08f7df255f82a44557dbb7b66e10cd3a39f04c89dda1a729efb26b18af9",
    "brython_stdlib.js": "b03456c4d14c52d0659d3cef47b8639ff2e8f58ea7baa0f303b4331cbb4baa57",
}


def runtime(name, expected, cache):
    file = cache / name
    if not file.exists():
        with urlopen(CDN + name, timeout=45) as response:
            data = response.read()
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError("Python runtime checksum mismatch: " + name)
        file.write_bytes(data)
    if hashlib.sha256(file.read_bytes()).hexdigest() != expected:
        raise ValueError("Cached Python runtime checksum mismatch: " + name)
    return file


def inline_python(path):
    code = path.read_text(encoding="utf-8")
    removed = set()
    for statement in ast.parse(code).body:
        if isinstance(statement, ast.ImportFrom) and statement.level:
            removed.update(range(statement.lineno, statement.end_lineno + 1))
    return "\n".join(line for i, line in enumerate(code.splitlines(), 1) if i not in removed)


def build(output, cache):
    output.mkdir(parents=True, exist_ok=True)
    cache.mkdir(parents=True, exist_ok=True)
    vendor = output / "vendor"
    vendor.mkdir(exist_ok=True)
    credits = ("Brython-LICENSE.txt", "OPEN-ART.txt")
    for name in credits:
        shutil.copyfile(ROOT / "third_party" / name, vendor / name)
    page = (ROOT / "index.html").read_text(encoding="utf-8")
    page = page.replace('<link rel="stylesheet" href="maplee/ui.css">', '<style>\n' +
                        (ROOT / "maplee/ui.css").read_text(encoding="utf-8") + '\n</style>')
    page = page.replace('<script src="maplee/request.js"></script>', '<script>\n' +
                        (ROOT/"maplee/request.js").read_text(encoding="utf-8") + '</script>')
    for name, expected in RUNTIME.items():
        shutil.copyfile(runtime(name, expected, cache), vendor / name)
        page = page.replace(CDN + name, "vendor/" + name)
    expect = "from maplee.ui import App\ngame_app = App()"
    if page.count(expect) != 1:
        raise ValueError("Expected one Python entry point")
    modules = "\n\n".join(inline_python(ROOT / "maplee" / (name + ".py"))
                            for name in ("gear_data", "wildlife_data", "combat_art", "content", "hunting", "engine", "render", "classic_skin", "windows", "lobby", "ui"))
    packed = modules + "\n\ngame_app = App()"
    if "</script" in packed.lower():
        raise ValueError("Unexpected HTML delimiter in Python source")
    compile(packed, "<browser app>", "exec")
    page = page.replace(expect, packed)
    assets = output / "assets"
    assets.mkdir(exist_ok=True)
    from maplee.content import IMAGES
    for name in IMAGES.values():
        shutil.copyfile(ROOT / "assets" / name, assets / name)
    (output / "index.html").write_text(page, encoding="utf-8")
    bundle = {}
    web_files = [output/"index.html", *(assets/name for name in IMAGES.values()),
                 *(vendor/name for name in (*RUNTIME,*credits))]
    for source in web_files:
        path = '/' + source.relative_to(output).as_posix()
        raw = source.read_bytes()
        kind = mimetypes.guess_type(source.name)[0] or "application/octet-stream"
        compressed = kind.startswith("text/") or source.suffix == ".js"
        blob = gzip.compress(raw,mtime=0) if compressed else raw
        bundle[path] = (kind,compressed,base64.b64encode(blob).decode("ascii"))
    worker = output / "server"
    worker.mkdir(exist_ok=True)
    main = (ROOT/"server/accounts.mjs").read_text().removeprefix('import { asset } from "./static.mjs";\n')
    static = (ROOT/"server/static.mjs").read_text()
    (worker/"index.js").write_text("const ASSETS = " + json.dumps(bundle) + ";\n" + static + "\n" + main)
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    parser.add_argument("--cache", type=Path, default=ROOT / ".cache" / "brython")
    arguments = parser.parse_args()
    print("Built", build(arguments.output, arguments.cache))
