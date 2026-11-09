"""Execute real dashboard scripts with a small DOM stub and missing data files."""

import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HARNESS = r'''
const fs = require("fs"), vm = require("vm");
const [root, lang, missing] = process.argv.slice(1);
class Element {
  constructor() { this.nodeType = 1; this.childNodes = []; this.dataset = {}; this.attrs = {}; this.clientWidth = 0; this.parentNode = {clientWidth: 0};
    this.classList = {add() {}, remove() {}, toggle() {}, contains() {return false}}; }
  hasAttribute(name) { return name in this.attrs; }
  setAttribute(name, value) { this.attrs[name] = value; }
  getAttribute(name) { return this.attrs[name]; }
  removeAttribute(name) { delete this.attrs[name]; }
  querySelectorAll() { return []; }
  addEventListener() {}
  getBoundingClientRect() { return {top: 0}; }
}
const els = new Map();
const el = id => {if (!els.has(id)) els.set(id, new Element()); return els.get(id);};
const docLink = new Element(); docLink.dataset = {doc: "docs/INSTALL"};
const toc = new Element(); toc.hash = "#overview";
const document = {getElementById: el, documentElement: new Element(), body: new Element(), title: "Camera ablations",
  querySelectorAll: selector => selector === "[data-doc]" ? [docLink] : selector === ".contents a" ? [toc] : [],
  querySelector: el};
const context = {document, window: {}, URLSearchParams, location: {search: "?lang=" + lang, protocol: "https:"},
  navigator: {language: lang}, MutationObserver: class {observe() {}}, addEventListener() {},
  matchMedia: () => ({matches: false}), localStorage: {getItem() {return null}, setItem() {}},
  fetch: () => Promise.resolve({ok: false}), requestAnimationFrame: fn => fn()};
vm.createContext(context);
for (const name of ["results", "followup"]) if (missing !== name)
  vm.runInContext(fs.readFileSync(root + "/dashboard/" + name + ".js", "utf8"), context);
if (missing === "blackout") delete context.window.BLACKOUT;
if (missing === "followup_core") delete context.window.FOLLOWUP;
if (missing === "wrist") delete context.window.FOLLOWUP.wrist_study;
vm.runInContext(fs.readFileSync(root + "/dashboard/app.js", "utf8"), context);
el("themeBtn").onclick();
console.log(JSON.stringify({keys: el("keys").innerHTML, theme: document.documentElement.dataset.theme,
  doc: docLink.href, p1: el("p1A").textContent, p2: el("p2Finding").textContent}));
'''


@pytest.mark.parametrize("lang", ["zh", "en"])
@pytest.mark.parametrize("missing", ["none", "results", "blackout", "followup_core", "followup", "wrist"])
def test_missing_data_keeps_navigation_and_other_results_usable(lang, missing):
    run = subprocess.run(["node", "-e", HARNESS, str(ROOT), lang, missing], capture_output=True, text=True, timeout=10)
    assert run.returncode == 0, run.stderr
    result = json.loads(run.stdout)
    assert result["theme"] == "dark"
    assert result["doc"].endswith("INSTALL.md" if lang == "en" else "INSTALL_CN.md")
    if missing in {"results", "blackout", "followup_core"}:
        assert ('role="status"' in result["keys"] and 'href="#resources"' in result["keys"])
        assert ("could not be loaded" if lang == "en" else "结果数据未加载") in result["keys"]
        assert "0 / 0" not in result["keys"]
    else:
        assert "53–56%" in result["keys"] and "27/27" in result["keys"]
        assert 'href="#engineering"' in result["keys"] and 'href="#single-camera"' in result["keys"]
        if missing == "wrist":
            assert "98.4 → 4.6" not in result["keys"]
            assert ("could not be loaded" if lang == "en" else "尚未加载") in result["keys"]
        else:
            assert "98.4 → 4.6%" in result["keys"]
        assert "5 / 5" not in result["keys"]
    if missing != "followup":
        assert result["p1"] == "73.3%" and "262/400" in result["p2"]
    else:
        assert ("could not be loaded" if lang == "en" else "未加载") in result["p2"]
