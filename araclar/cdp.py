"""
Başsız Chrome'u DevTools protokolüyle (CDP) süren küçük yardımcı. Yardım sayfasının ekran
görüntüleri için (araclar/yardim_goruntuleri.py). Ek paket gerekmez: `websockets` (projede var).

    with Tarayici() as t:
        t.cerez("sessionid", "...", "http://localhost:8781")
        t.telefon(tema="koyu")
        t.git("http://localhost:8781/sozluk/")
        t.js("document.querySelector('#ara').focus()")
        t.kaydet("cikti.webp", y=0, yukseklik=812)
"""

import asyncio
import base64
import json
import os
import shutil
import subprocess
import tempfile
import time
import urllib.request

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
GENISLIK, YUKSEKLIK = 375, 812           # telefon görünümü (CSS piksel)
OLCEK = 500 / 375                        # görüntü 500 px genişlikte çıkar


class Tarayici:
    def __init__(self, port=9333):
        self.port = port
        self.no = 0
        self.dongu = asyncio.new_event_loop()

    def __enter__(self):
        import websockets
        self.klasor = tempfile.mkdtemp(prefix="lv-chrome-")
        self.surec = subprocess.Popen(
            [CHROME, "--headless=new", f"--remote-debugging-port={self.port}", f"--user-data-dir={self.klasor}",
             "--hide-scrollbars", "--no-first-run", "--no-default-browser-check", "--mute-audio",
             "--disable-features=Translate", "about:blank"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(100):
            try:
                hedefler = json.load(urllib.request.urlopen(f"http://127.0.0.1:{self.port}/json/list"))
                sayfa = next(h for h in hedefler if h["type"] == "page")
                break
            except Exception:  # noqa: BLE001
                time.sleep(0.1)
        self.ws = self.dongu.run_until_complete(websockets.connect(sayfa["webSocketDebuggerUrl"], max_size=None))
        for alan in ("Page", "Runtime", "Network"):
            self.komut(f"{alan}.enable")
        return self

    def __exit__(self, *hata):
        self.dongu.run_until_complete(self.ws.close())
        self.surec.terminate()
        self.surec.wait(timeout=10)
        shutil.rmtree(self.klasor, ignore_errors=True)

    # --- protokol ---
    def komut(self, yontem, **parametre):
        return self.dongu.run_until_complete(self._komut(yontem, parametre))

    async def _komut(self, yontem, parametre):
        self.no += 1
        no = self.no
        await self.ws.send(json.dumps({"id": no, "method": yontem, "params": parametre}))
        while True:
            mesaj = json.loads(await self.ws.recv())
            if mesaj.get("id") == no:
                if "error" in mesaj:
                    raise RuntimeError(f"{yontem}: {mesaj['error']}")
                return mesaj.get("result", {})

    # --- kolaylıklar ---
    def cerez(self, ad, deger, adres):
        self.komut("Network.setCookie", name=ad, value=deger, url=adres)

    def telefon(self, tema="acik", yukseklik=YUKSEKLIK):
        self.komut("Emulation.setDeviceMetricsOverride", width=GENISLIK, height=yukseklik,
                   deviceScaleFactor=OLCEK, mobile=True)
        self.komut("Emulation.setTouchEmulationEnabled", enabled=True, maxTouchPoints=5)
        self.komut("Emulation.setEmulatedMedia", features=[
            {"name": "prefers-color-scheme", "value": "dark" if tema == "koyu" else "light"},
            {"name": "prefers-reduced-motion", "value": "reduce"}])

    def js(self, ifade, bekle=True):
        sonuc = self.komut("Runtime.evaluate", expression=ifade, awaitPromise=bekle, returnByValue=True)
        if "exceptionDetails" in sonuc:
            ayrinti = sonuc["exceptionDetails"]
            aciklama = (ayrinti.get("exception") or {}).get("description") or ayrinti.get("text")
            raise RuntimeError(f"JS hatası: {aciklama} — {ifade[:120]}")
        return sonuc.get("result", {}).get("value")

    def git(self, adres, bekleme=0.6):
        self.komut("Page.navigate", url=adres)
        for _ in range(200):
            time.sleep(0.05)
            try:
                if self.js("document.readyState") == "complete":
                    break
            except RuntimeError:
                pass
        self.js("document.fonts ? document.fonts.ready.then(() => true) : true")
        time.sleep(bekleme)

    def tikla(self, x, y):
        for tur in ("mousePressed", "mouseReleased"):
            self.komut("Input.dispatchMouseEvent", type=tur, x=x, y=y, button="left", clickCount=1)

    def kaydet(self, yol, y=0, yukseklik=YUKSEKLIK, kalite=88):
        """Sayfanın görünen alanından (y, yükseklik CSS px) 500 px genişlikte webp."""
        # clip belge koordinatındadır: sayfa kaydırılmışsa görünen alanın başı scrollY'dir
        y += self.js("window.visualViewport ? window.visualViewport.pageTop : window.scrollY") or 0
        veri = self.komut("Page.captureScreenshot", format="webp", quality=kalite,
                          clip={"x": 0, "y": y, "width": GENISLIK, "height": yukseklik, "scale": 1},
                          captureBeyondViewport=False)
        os.makedirs(os.path.dirname(yol) or ".", exist_ok=True)
        with open(yol, "wb") as f:
            f.write(base64.b64decode(veri["data"]))
