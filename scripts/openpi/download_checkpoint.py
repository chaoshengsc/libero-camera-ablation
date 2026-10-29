"""从 OpenPI 公开存储桶下载一个检查点目录,逐个文件用桶列表里的 md5 校验;已下载且校验通过的文件跳过,可断点续跑。
用法: python download_checkpoint.py <桶内前缀,如 checkpoints/pi0_libero> <本地目录>
只用标准库(工作站没有 gsutil / curl)。"""
import base64
import hashlib
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

BUCKET = "openpi-assets"
PREFIX, OUT = sys.argv[1].rstrip("/") + "/", Path(sys.argv[2])


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 24), b""):
            h.update(chunk)
    return base64.b64encode(h.digest()).decode()


items, token = [], None
while True:
    q = {"prefix": PREFIX, "fields": "items(name,size,md5Hash,updated),nextPageToken"} | ({"pageToken": token} if token else {})
    with urllib.request.urlopen(f"https://storage.googleapis.com/storage/v1/b/{BUCKET}/o?{urllib.parse.urlencode(q)}", timeout=60) as r:
        page = json.load(r)
    items += page.get("items", [])
    token = page.get("nextPageToken")
    if not token:
        break
print(f"{len(items)} files, {sum(int(i['size']) for i in items) / 1e9:.2f} GB, updated {min(i['updated'] for i in items)[:10]}", flush=True)
(OUT.parent / (OUT.name + ".listing.json")).write_text(json.dumps(items, indent=1))
for i in items:
    dst = OUT / i["name"][len(PREFIX):]
    if dst.exists() and dst.stat().st_size == int(i["size"]) and md5(dst) == i["md5Hash"]:
        continue
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_name(dst.name + ".part")
    urllib.request.urlretrieve(f"https://storage.googleapis.com/{BUCKET}/{urllib.parse.quote(i['name'])}", tmp)
    assert md5(tmp) == i["md5Hash"], f"md5 mismatch: {i['name']}"
    tmp.rename(dst)
    print("ok", i["name"], i["size"], flush=True)
print("DONE all md5 verified", flush=True)
