"""
FonRadar + KursRadar + DiştakipRadar
FINAL VERSION v4 — Tüm Kosova Diş Depoları + OMFS Dernekleri
GitHub Actions Edition — PC gerekmez.

Kosova Depo Listesi (14 firma):
  Allianz Dental, Bora Dental, MatkosPharm, Koslabor,
  Medident, A&M Technology, Matrix Dent, Erioni Dent,
  Hemna Group, Avas Shtime, Biohit, Gamma R Shpk,
  Vizion Dental Kosova, Vizion Dent Sh.p.k.
"""

import requests
import time
import os
import statistics
import xml.etree.ElementTree as ET
import re
from datetime import datetime, date

TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
YAHOO_BASE = "https://query1.finance.yahoo.com/v8/finance/chart"

# ══════════════════════════════════════════════════════════════════════
#  ETF LİSTESİ
# ══════════════════════════════════════════════════════════════════════
ETF_PORTFOY = {
    "IGLN.L":  "🟡 Fiziksel Altın",
    "GDX":     "🟡 Altın Madencileri",
    "IWDA.L":  "📈 Global Hisse",
    "EXW1.DE": "📈 Avrupa Hisse",
    "IUIT.L":  "📈 Teknoloji",
    "IEAG.L":  "💵 Euro Tahvil",
    "IDTL.L":  "💵 ABD Tahvil",
}

# ══════════════════════════════════════════════════════════════════════
#  KOSOVA DİŞ DEPOLARI — TAM LİSTE (14 firma)
#  izleme: "web" = web sitesi tara | "arama" = DuckDuckGo ile ara
# ══════════════════════════════════════════════════════════════════════
KOSOVA_DEPOLAR = [
    # ── Web sitesi olanlar ────────────────────────────────────────────
    {
        "isim":   "Allianz Dental Kosovo",
        "izleme": "web",
        "url":    "https://www.allianzdental.com/en",
        "ig":     None,
        "not":    "3D tarayıcı, dental ünit, kurs düzenler ⭐",
        "anahtar": ["course", "training", "kursus", "trajnim", "new", "3d",
                    "scanner", "implant", "ofertë", "price", "çmim", "promotion", "event"],
    },
    {
        "isim":   "Bora Dental",
        "izleme": "web",
        "url":    "https://bora-dental.com/",
        "ig":     "@boradental1",
        "not":    "Dentsply Sirona, Dürr, Melag, Fotona distribütörü",
        "anahtar": ["kurs", "trajnim", "course", "training", "promotion",
                    "ofertë", "new", "çmim", "price", "discount", "event"],
    },
    {
        "isim":   "MatkosPharm",
        "izleme": "web",
        "url":    "https://www.matkospharm.com/",
        "ig":     None,
        "not":    "500+ klinik ağı, ilaç ve dental malzeme",
        "anahtar": ["promotion", "kurs", "training", "ofertë", "new",
                    "çmim", "price", "discount", "trajnim", "product"],
    },
    {
        "isim":   "Koslabor",
        "izleme": "web",
        "url":    "http://www.koslabor.com/",
        "ig":     None,
        "not":    "NSK distribütörü, dental el aletleri",
        "anahtar": ["kurs", "course", "training", "ofertë", "new",
                    "price", "dental", "handpiece", "product"],
    },

    # ── Yalnızca arama ile izlenenler ────────────────────────────────
    {
        "isim":   "Medident Kosovo",
        "izleme": "arama",
        "url":    None,
        "ig":     None,
        "not":    "NSK distribütörü, dental el aletleri",
        "sorgu":  "Medident Kosovo dental depot new product promotion 2025",
    },
    {
        "isim":   "A&M Technology Kosovo",
        "izleme": "arama",
        "url":    None,
        "ig":     None,
        "not":    "Dental teknoloji çözümleri",
        "sorgu":  "AM Technology dental Kosovo Prishtina equipment supply",
    },
    {
        "isim":   "Matrix Dent Kosovo",
        "izleme": "arama",
        "url":    None,
        "ig":     None,
        "not":    "Diş malzeme deposu",
        "sorgu":  "Matrix Dent Kosovo dental supply equipment Prishtina",
    },
    {
        "isim":   "Erioni Dent Kosovo",
        "izleme": "arama",
        "url":    None,
        "ig":     None,
        "not":    "Diş deposu",
        "sorgu":  "Erioni Dent Kosovo dental depot supply Prishtina",
    },
    {
        "isim":   "Hemna Group Kosovo",
        "izleme": "arama",
        "url":    None,
        "ig":     None,
        "not":    "Medikal ve dental grup",
        "sorgu":  "Hemna Group Kosovo dental medical equipment supply",
    },
    {
        "isim":   "Avas Shtime Kosovo",
        "izleme": "arama",
        "url":    None,
        "ig":     None,
        "not":    "Shtime bölgesi dental deposu",
        "sorgu":  "Avas Shtime Kosovo dental depot supply equipment",
    },
    {
        "isim":   "Biohit Kosovo",
        "izleme": "arama",
        "url":    None,
        "ig":     None,
        "not":    "Dental ve medikal malzeme",
        "sorgu":  "Biohit Kosovo dental medical supply equipment Prishtina",
    },
    {
        "isim":   "Gamma R Shpk Kosovo",
        "izleme": "arama",
        "url":    None,
        "ig":     None,
        "not":    "Dental malzeme şirketi",
        "sorgu":  "Gamma R Shpk Kosovo dental equipment supply",
    },
    {
        "isim":   "Vizion Dental Kosova",
        "izleme": "arama",
        "url":    None,
        "ig":     None,
        "not":    "Dental deposu",
        "sorgu":  "Vizion Dental Kosova dental supply depot equipment",
    },
    {
        "isim":   "Vizion Dent Sh.p.k.",
        "izleme": "arama",
        "url":    None,
        "ig":     None,
        "not":    "Dental deposu / klinik",
        "sorgu":  "\"Vizion Dent\" Shpk Kosovo dental supply equipment Prishtina",
    },
]

# ══════════════════════════════════════════════════════════════════════
#  TEDARİKÇİ MARKALAR — RSS + web
# ══════════════════════════════════════════════════════════════════════
TEDARIKCILAR = [
    {
        "isim": "Dental Tribune RSS",
        "url":  "https://www.dental-tribune.com/feed/",
        "rss":  True,
        "anahtar": ["course", "congress", "education", "balkans", "turkey", "kosovo",
                    "implant", "aesthetic", "osstem", "nobel", "straumann", "training"],
    },
    {
        "isim": "Osstem Education",
        "url":  "https://www.osstem.com/en/news",
        "rss":  False,
        "anahtar": ["course", "training", "education", "promotion", "new product", "event"],
    },
    {
        "isim": "Nobel Biocare Education",
        "url":  "https://www.nobelbiocare.com/en-int/education",
        "rss":  False,
        "anahtar": ["course", "hands-on", "workshop", "webinar", "live surgery", "congress"],
    },
    {
        "isim": "ITI Courses",
        "url":  "https://www.iti.org/education/courses",
        "rss":  False,
        "anahtar": ["course", "workshop", "hands-on", "symposium", "balkans", "turkey"],
    },
    {
        "isim": "EAO Events",
        "url":  "https://www.eao.org/education/courses-and-events",
        "rss":  False,
        "anahtar": ["course", "training", "congress", "balkans", "turkey"],
    },

    # ── MAKSİLLOFASİYAL CERRAHİ DERNEKLERİ ─────────────────────────
    {
        "isim": "TAOMS — Türk Oral & Maksillofasiyal Cerrahi Derneği",
        "url":  "https://www.taoms.org/",
        "rss":  False,
        "anahtar": ["congress", "kurs", "course", "training", "event", "toplanti",
                    "sempozyum", "symposium", "kayit", "register", "2025", "2026"],
    },
    {
        "isim": "AO CMF — Cranio Maxillofacial",
        "url":  "https://www.aocmf.org/education/courses.html",
        "rss":  False,
        "anahtar": ["course", "hands-on", "workshop", "training", "seminar",
                    "faculty", "register", "europe", "turkey", "balkans", "2025", "2026"],
    },
    {
        "isim": "EACMFS — European Assoc. Cranio-Maxillo-Facial Surgery",
        "url":  "https://www.eacmfs.org/events/",
        "rss":  False,
        "anahtar": ["congress", "course", "event", "workshop", "symposium",
                    "register", "deadline", "abstract", "2025", "2026"],
    },
    {
        "isim": "EACMFS 2026 Congress — Athens",
        "url":  "https://www.eacmfs-congress.com/EACMFS2026",
        "rss":  False,
        "anahtar": ["registration", "abstract", "course", "deadline", "programme",
                    "speaker", "workshop", "early bird", "2026"],
    },
    {
        "isim": "IAOMS — International Assoc. Oral & Maxillofacial Surgeons",
        "url":  "https://www.iaoms.org/news-events/",
        "rss":  False,
        "anahtar": ["congress", "course", "event", "webinar", "training",
                    "fellowship", "register", "deadline", "2025", "2026", "2027"],
    },
    {
        "isim": "ICOMS 2027 — Berlin",
        "url":  "https://icoms.iaoms.org/",
        "rss":  False,
        "anahtar": ["registration", "abstract", "course", "deadline", "programme",
                    "early bird", "save the date", "berlin", "2027"],
    },
    {
        "isim": "ICMFS — International College of Maxillofacial Surgeons",
        "url":  "https://www.icmfs.org/",
        "rss":  False,
        "anahtar": ["congress", "course", "event", "meeting", "fellowship",
                    "register", "training", "2025", "2026"],
    },
]


# ══════════════════════════════════════════════════════════════════════
#  📊  ETF MODÜLÜ
# ══════════════════════════════════════════════════════════════════════

def etf_veri_cek(sembol):
    try:
        r = requests.get(f"{YAHOO_BASE}/{sembol}",
                         params={"range": "30d", "interval": "1d"},
                         headers=HEADERS, timeout=15)
        closes = r.json()["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        gecerli = [c for c in closes if c is not None]
        return gecerli if len(gecerli) >= 5 else None
    except:
        return None

def rsi_hesapla(f, p=14):
    if len(f) < p + 1: return 50.0
    d = [f[i] - f[i-1] for i in range(1, len(f))]
    k = statistics.mean([x for x in d[-p:] if x > 0] or [0.001])
    y = statistics.mean([-x for x in d[-p:] if x < 0] or [0.001])
    return round(100 - 100 / (1 + k / y), 1)

def guven_hesapla(rsi, t5, t20, ma5u, ma20u, vol):
    p = 0
    if 35 <= rsi <= 65: p += 1.5
    elif rsi < 30: p += 0.8
    if t5 > 0 and t20 > 0: p += 2
    elif t5 > 0: p += 0.8
    if ma5u and ma20u: p += 2
    elif ma5u: p += 0.8
    if vol < 1.0: p += 1
    elif vol < 2.0: p += 0.5
    return min(int(p / 7 * 100), 100)

def etf_analiz(sembol, fiyatlar):
    f = fiyatlar[-1]; fd = fiyatlar[-2]
    f5  = fiyatlar[-6]  if len(fiyatlar) >= 6  else fiyatlar[0]
    f20 = fiyatlar[-21] if len(fiyatlar) >= 21 else fiyatlar[0]
    gun = (f - fd) / fd * 100
    t5  = (f - f5)  / f5  * 100
    t20 = (f - f20) / f20 * 100
    rsi = rsi_hesapla(fiyatlar)
    ma5  = statistics.mean(fiyatlar[-5:])
    ma20 = statistics.mean(fiyatlar[-20:]) if len(fiyatlar) >= 20 else statistics.mean(fiyatlar)
    dg   = [abs((fiyatlar[i]-fiyatlar[i-1])/fiyatlar[i-1]*100) for i in range(1, len(fiyatlar))]
    vol  = statistics.stdev(dg[-10:]) if len(dg) >= 3 else 0
    g    = guven_hesapla(rsi, t5, t20, f > ma5, f > ma20, vol)

    if   gun >= 0.3 and t5 >= 1.0 and g >= 60: sinyal = "🟢 AL"
    elif gun <= -0.3 and t5 <= -1.0 and g < 40: sinyal = "🔴 SAT"
    elif g >= 68: sinyal = "🟢 AL"
    elif g <= 32: sinyal = "🔴 SAT"
    else:         sinyal = "🟡 BEKLE"

    stop = round(min(fiyatlar[-7:]) * 0.98, 4) if len(fiyatlar) >= 7 else round(f * 0.95, 4)
    bar  = "█" * (g // 10) + "░" * (10 - g // 10)
    return {"sembol": sembol, "fiyat": round(f, 3), "gunluk": round(gun, 2),
            "rsi": rsi, "guven": g, "bar": bar, "sinyal": sinyal, "stop": stop}

def etf_raporu(sonuclar):
    al    = [s for s in sonuclar if "AL"    in s["sinyal"]]
    sat   = [s for s in sonuclar if "SAT"   in s["sinyal"]]
    bekle = [s for s in sonuclar if "BEKLE" in s["sinyal"]]
    ort   = int(statistics.mean(s["guven"] for s in sonuclar)) if sonuclar else 0
    now   = datetime.now().strftime('%d.%m.%Y %H:%M')
    msg   = f"📊 *ETF SİNYAL RAPORU*\n🗓 {now}\n\n"
    if al:
        msg += f"🟢 *AL* ({len(al)})\n"
        for s in sorted(al, key=lambda x: x["guven"], reverse=True):
            kat = ETF_PORTFOY.get(s['sembol'], '')
            msg += (f"*{s['sembol']}* — {kat}\n"
                    f"  {s['bar']} {s['guven']}%\n"
                    f"  Bugün: {s['gunluk']:+.2f}% | RSI: {s['rsi']}\n"
                    f"  ⛔ Stop: {s['stop']}\n\n")
    if sat:
        msg += f"🔴 *SAT* ({len(sat)})\n"
        for s in sorted(sat, key=lambda x: x["guven"]):
            msg += f"  `{s['sembol']}` {s['gunluk']:+.2f}% | Güven: {s['guven']}%\n"
        msg += "\n"
    if bekle:
        msg += f"🟡 *BEKLE:* " + "  ".join(f"`{s['sembol']}`" for s in bekle) + "\n\n"
    genel = "✅ Pozitif" if ort >= 65 else ("⚠️ Karışık" if ort >= 45 else "🚨 Olumsuz")
    msg += f"━━━━━━━━━━━━━━━\nGenel: {ort}% — {genel}\n"
    msg += "_Güven %60 altı sinyali atla. Stop-loss kullan._"
    return msg


# ══════════════════════════════════════════════════════════════════════
#  🦷  DİŞ DEPOSU TAKİP MODÜLÜ
# ══════════════════════════════════════════════════════════════════════

def temizle_html(metin):
    """HTML tag'lerini kaldırır, boşlukları düzenler."""
    temiz = re.sub(r'<[^>]+>', ' ', metin)
    return ' '.join(temiz.split())

def web_tara(url, anahtar_kelimeler):
    """Web sayfasını tarar, anahtar kelime içeren bağlamı döndürür."""
    bulunanlar = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        metin_kucuk = r.text.lower()
        for k in anahtar_kelimeler:
            idx = metin_kucuk.find(k.lower())
            if idx != -1:
                baslangic = max(0, idx - 50)
                bitis     = min(len(r.text), idx + 120)
                parcali   = temizle_html(r.text[baslangic:bitis])[:100]
                if len(parcali) > 20:
                    bulunanlar.append({"baslik": f"{k.title()}: {parcali}", "url": url})
                    break  # Kaynak başına 1 sonuç yeter
    except Exception as e:
        print(f"    web hata ({url[:40]}): {e}")
    return bulunanlar

def rss_tara(url, anahtar_kelimeler):
    """RSS feed tarar, anahtar kelime eşleşen haberleri döndürür."""
    bulunanlar = []
    try:
        r    = requests.get(url, headers=HEADERS, timeout=15)
        root = ET.fromstring(r.content)
        for item in root.findall(".//item")[:20]:
            baslik = (item.findtext("title") or "")
            link   = (item.findtext("link")  or url)
            desc   = (item.findtext("description") or "")
            metin  = (baslik + " " + desc).lower()
            if any(k.lower() in metin for k in anahtar_kelimeler):
                bulunanlar.append({"baslik": baslik[:80], "url": link})
    except Exception as e:
        print(f"    RSS hata ({url[:40]}): {e}")
    return bulunanlar[:5]

def duckduckgo_ara(sorgu):
    """DuckDuckGo Instant API — ücretsiz, key gerektirmez."""
    bulunanlar = []
    try:
        r    = requests.get("https://api.duckduckgo.com/",
                            params={"q": sorgu, "format": "json",
                                    "no_redirect": 1, "no_html": 1, "skip_disambig": 1},
                            headers=HEADERS, timeout=12)
        data = r.json()
        if data.get("AbstractText") and data.get("AbstractURL"):
            bulunanlar.append({"baslik": (data.get("Heading") or sorgu)[:70],
                               "url": data["AbstractURL"]})
        for item in data.get("RelatedTopics", [])[:3]:
            if isinstance(item, dict) and item.get("FirstURL") and item.get("Text"):
                bulunanlar.append({"baslik": item["Text"][:70],
                                   "url": item["FirstURL"]})
    except Exception as e:
        print(f"    DDG hata: {e}")
    return bulunanlar

def dis_deposu_raporu():
    tarih = datetime.now().strftime('%d.%m.%Y')
    msg   = f"🦷 *KOSOVA DİŞ DEPOSU TAKİP*\n🗓 {tarih}\n"
    msg  += "━━━━━━━━━━━━━━━━━━━━\n\n"

    # ── Kosova Depoları ───────────────────────────────────────────────
    msg += "🇽🇰 *KOSOVA DİŞ DEPOLARI* (14 firma)\n\n"
    depo_toplam = 0

    for depo in KOSOVA_DEPOLAR:
        print(f"  📡 {depo['isim']} taranıyor...")
        bulunanlar = []

        if depo["izleme"] == "web" and depo["url"]:
            bulunanlar = web_tara(depo["url"], depo["anahtar"])
        elif depo["izleme"] == "arama":
            bulunanlar = duckduckgo_ara(depo["sorgu"])
        time.sleep(0.8)

        isim_e = (depo["isim"]
                  
                  )
        not_e  = (depo.get("not", "")
                  
                  .replace("⭐", "⭐"))
        ig_str = f" | IG: `{depo['ig']}`" if depo.get("ig") else ""

        if bulunanlar:
            msg += f"*{isim_e}*{ig_str}\n_{not_e}_\n"
            for b in bulunanlar[:2]:
                baslik_e = (b["baslik"]
                            
                            
                            
                            )
                msg += f"  ▸ [{baslik_e}]({b['url']})\n"
            msg += "\n"
            depo_toplam += len(bulunanlar)
        else:
            # Bulunamasa da firma adını ve web/IG linkini yaz
            url_str = depo.get("url", "")
            if url_str:
                msg += f"*{isim_e}* — [Web sitesi]({url_str}){ig_str}\n_{not_e}_\n_Bugün yeni içerik yok_\n\n"
            else:
                msg += f"*{isim_e}*{ig_str}\n_{not_e}_\n_Online varlık bulunamadı — yerel takip önerilir_\n\n"

    # ── Tedarikçi Markalar ────────────────────────────────────────────
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    msg += "🏭 *TEDARİKÇİ MARKALAR*\n\n"

    for kaynak in TEDARIKCILAR:
        print(f"  📡 {kaynak['isim']} taranıyor...")
        if kaynak["rss"]:
            bulunanlar = rss_tara(kaynak["url"], kaynak["anahtar"])
        else:
            bulunanlar = web_tara(kaynak["url"], kaynak["anahtar"])
        time.sleep(0.8)

        if bulunanlar:
            isim_e = kaynak["isim"]
            msg += f"*{isim_e}*\n"
            for b in bulunanlar[:2]:
                baslik_e = (b["baslik"]
                            
                            
                            )
                msg += f"  ▸ [{baslik_e}]({b['url']})\n"
            msg += "\n"

    # ── Sabit Kaynaklar ───────────────────────────────────────────────
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    msg += "📌 *Sabit Takip Kaynakları:*\n"
    sabitler = [
        ("Allianz Dental Kosovo",   "https://www.allianzdental.com/en"),
        ("Bora Dental",             "https://bora-dental.com/"),
        ("MatkosPharm",             "https://www.matkospharm.com/"),
        ("Koslabor",                "http://www.koslabor.com/"),
        ("Osstem Education",        "https://www.osstem.com/en/education"),
        ("Nobel Biocare Education", "https://www.nobelbiocare.com/en-int/education"),
        ("ITI Courses",             "https://www.iti.org/education/courses"),
        ("EAO Events",              "https://www.eao.org/education"),
        ("Dental Tribune",          "https://www.dental-tribune.com"),
        # ── Maksillofasiyal Cerrahi ──────────────────────────────────
        ("TAOMS",                   "https://www.taoms.org/"),
        ("AO CMF Courses",          "https://www.aocmf.org/education/courses.html"),
        ("EACMFS",                  "https://www.eacmfs.org/events/"),
        ("EACMFS 2026 — Atina",     "https://www.eacmfs-congress.com/EACMFS2026"),
        ("IAOMS Events",            "https://www.iaoms.org/news-events/"),
        ("ICOMS 2027 — Berlin",     "https://icoms.iaoms.org/"),
        ("ICMFS",                   "https://www.icmfs.org/"),
    ]
    for isim, url in sabitler:
        isim_e = isim
        msg += f"▸ [{isim_e}]({url})\n"

    return msg


# ══════════════════════════════════════════════════════════════════════
#  🎓  KURS MODÜLÜ
# ══════════════════════════════════════════════════════════════════════

def kurs_ara_ddg(sorgu):
    try:
        r    = requests.get("https://api.duckduckgo.com/",
                            params={"q": sorgu, "format": "json",
                                    "no_redirect": 1, "no_html": 1, "skip_disambig": 1},
                            headers=HEADERS, timeout=12)
        data = r.json()
        sonuclar = []
        if data.get("AbstractText") and data.get("AbstractURL"):
            sonuclar.append({"baslik": (data.get("Heading") or sorgu)[:70],
                             "url": data["AbstractURL"]})
        for item in data.get("RelatedTopics", [])[:3]:
            if isinstance(item, dict) and item.get("FirstURL"):
                sonuclar.append({"baslik": (item.get("Text") or "")[:70],
                                 "url": item["FirstURL"]})
        return sonuclar
    except:
        return []

def kurs_raporu():
    yil = datetime.now().year
    kategoriler = {
        "🔪 PLASTİK & CERRAHİ": [
            f"rhinoplasty surgery course Turkey {yil}",
            f"facelift blepharoplasty training Istanbul {yil}",
            f"plastic surgery congress Balkans {yil}",
        ],
        "😁 DİŞ & İMPLANT": [
            f"dental implant course Turkey Balkans {yil}",
            f"All-on-4 training Istanbul {yil}",
            f"smile design aesthetic dentistry course {yil}",
            f"ITI EAO dental course Europe {yil}",
        ],
        "✨ ESTETİK TIP": [
            f"IMCAS aesthetic surgery congress {yil}",
            f"aesthetic medicine course Turkey Balkans {yil}",
        ],
    }
    tarih = datetime.now().strftime('%d.%m.%Y')
    msg   = f"🎓 *CERRAHİ & ESTETİK & DİŞ KURSLARI*\n"
    msg  += f"📍 Türkiye & Balkanlar | 🗓 {tarih}\n\n"
    toplam = 0
    for kat, aramalar in kategoriler.items():
        goruldu = set(); bulunanlar = []
        for a in aramalar:
            for s in kurs_ara_ddg(a):
                if s["url"] not in goruldu:
                    goruldu.add(s["url"]); bulunanlar.append(s)
            time.sleep(0.6)
        if bulunanlar:
            msg += f"*{kat}*\n"
            for k in bulunanlar[:3]:
                b = (k["baslik"]
                     
                     
                     )
                msg += f"▸ [{b}]({k['url']})\n"
                toplam += 1
            msg += "\n"
    msg += f"_Toplam {toplam} kurs bulundu._"
    return msg


# ══════════════════════════════════════════════════════════════════════
#  📰  KOSOVA HABER + ODA STOMATOLOGJIKE MODÜLÜ
# ══════════════════════════════════════════════════════════════════════

HABER_KAYNAKLARI = [
    {
        "isim": "Koha.net",
        "rss":  "https://www.koha.net/feed/",
        "anahtar": ["dental", "stomatolog", "shëndet", "mjekësi", "implant",
                    "kurs", "trajnim", "spital", "klinik"],
    },
    {
        "isim": "Gazeta Blic",
        "rss":  "https://gazetablic.com/feed/",
        "anahtar": ["dental", "stomatolog", "shëndet", "mjekësi",
                    "kurs", "trajnim", "klinik", "spital"],
    },
]

ODA_STOMATOLOGJIKE = {
    "isim":     "Oda e Stomatologeve te Kosoves",
    "facebook": "https://www.facebook.com/odastomatologjike",
    "sorgu":    "Oda Stomatologjike Kosovo dental news announcement 2026",
}


def haber_raporu():
    """Koha.net ve Gazeta Blic RSS + Oda Stomatologjike haberleri."""
    tarih = datetime.now().strftime("%d.%m.%Y")
    msg   = f"📰 *KOSOVA HABERLERI & ODA STOMATOLOGJIKE*\n"
    msg  += f"🗓 {tarih}\n"
    msg  += "━━━━━━━━━━━━━━━━━━━━\n\n"

    toplam = 0

    # ── Haber siteleri RSS ────────────────────────────────────────────
    for kaynak in HABER_KAYNAKLARI:
        print(f"  📰 {kaynak['isim']} taranıyor...")
        bulunanlar = rss_tara(kaynak["rss"], kaynak["anahtar"])
        time.sleep(0.8)

        if bulunanlar:
            isim_e = kaynak["isim"].replace(".", "\\.")
            msg += f"*{isim_e}*\n"
            for b in bulunanlar[:3]:
                baslik_e = (b["baslik"]
                            .replace("*", "")
                            .replace("[", "")
                            .replace("]", "")
                            .replace("_", ""))[:70]
                msg += f"  ▸ [{baslik_e}]({b['url']})\n"
                toplam += 1
            msg += "\n"
        else:
            # RSS çalışmazsa DuckDuckGo ile ara
            print(f"    RSS yok, DuckDuckGo deneniyor...")
            sonuclar = duckduckgo_ara(f"{kaynak['isim']} dental stomatolog Kosovo 2026")
            if sonuclar:
                isim_e = kaynak["isim"].replace(".", "\\.")
                msg += f"*{isim_e}*\n"
                for s in sonuclar[:2]:
                    baslik_e = s["baslik"][:70].replace("*", "").replace("[", "").replace("]", "")
                    msg += f"  ▸ [{baslik_e}]({s['url']})\n"
                    toplam += 1
                msg += "\n"
            time.sleep(0.5)

    # ── Oda Stomatologjike ────────────────────────────────────────────
    print(f"  🦷 Oda Stomatologjike taranıyor...")
    oda_sonuclari = duckduckgo_ara(ODA_STOMATOLOGJIKE["sorgu"])
    time.sleep(0.8)

    msg += "*Oda e Stomatologeve te Kosoves*\n"
    msg += f"  ▸ [Facebook Sayfasi]({ODA_STOMATOLOGJIKE['facebook']}) — bugun kontrol et\n"

    if oda_sonuclari:
        for s in oda_sonuclari[:2]:
            baslik_e = s["baslik"][:70].replace("*", "").replace("[", "").replace("]", "")
            msg += f"  ▸ [{baslik_e}]({s['url']})\n"
            toplam += 1

    msg += "\n━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"_Toplam {toplam} haber/duyuru._"
    return msg


# ══════════════════════════════════════════════════════════════════════
#  📱  INSTAGRAM TAKİP HATIRLATMASI
# ══════════════════════════════════════════════════════════════════════

def instagram_hatirlatma():
    gun = datetime.now().strftime("%d.%m.%Y")
    msg  = f"📱 *INSTAGRAM TAKİP LİSTESİ*\n"
    msg += f"🗓 {gun} — Bugün kontrol et\n\n"

    msg += "*🇽🇰 KOSOVA DİŞ DEPOLARI*\n"
    kosova_ig = [
        ("Bora Dental",          "https://www.instagram.com/boradental1/"),
        ("Allianz Dental Kosovo", "https://www.instagram.com/allianzdental/"),
        ("MatkosPharm",          "https://www.instagram.com/matkospharm/"),
        ("Curaprox Kosova",      "https://www.instagram.com/curaproxkosova/"),
    ]
    for isim, url in kosova_ig:
        msg += f"  ▸ [{isim}]({url})\n"

    msg += "\n*🇹🇷 TÜRKİYE DİŞ DEPOLARI*\n"
    turkiye_ig = [
        ("Onur Dental",      "https://www.instagram.com/onurdisdeposu/"),
        ("Catak Dis Deposu", "https://www.instagram.com/catakdisdeposu/"),
        ("Guney Dis",        "https://www.instagram.com/guneydis/"),
    ]
    for isim, url in turkiye_ig:
        msg += f"  ▸ [{isim}]({url})\n"

    msg += "\n*🏭 TEDARİKÇİ MARKALAR*\n"
    tedarikci_ig = [
        ("Osstem Implant",   "https://www.instagram.com/osstemimplant/"),
        ("Nobel Biocare",    "https://www.instagram.com/nobelbiocare/"),
        ("Straumann Group",  "https://www.instagram.com/straumanngroup/"),
        ("Dentsply Sirona",  "https://www.instagram.com/dentsplysirona/"),
        ("GC Europe",        "https://www.instagram.com/gceurope/"),
    ]
    for isim, url in tedarikci_ig:
        msg += f"  ▸ [{isim}]({url})\n"

    msg += "\n*🎓 DERNEKLER & KONGRE*\n"
    kongre_ig = [
        ("TAOMS",   "https://www.instagram.com/taoms_official/"),
        ("EACMFS",  "https://www.instagram.com/eacmfs/"),
        ("IAOMS",   "https://www.instagram.com/iaoms_official/"),
        ("AO CMF",  "https://www.instagram.com/aocmf/"),
        ("ITI",     "https://www.instagram.com/iti_dental/"),
        ("EAO",     "https://www.instagram.com/eao_implantology/"),
    ]
    for isim, url in kongre_ig:
        msg += f"  ▸ [{isim}]({url})\n"

    msg += "\n_Linke tikla, son paylasimlari kontrol et._"

    # Telegram Kanalları
    msg += "\n\n*📢 TAKİP ET — TELEGRAM KANALLARI*\n"
    msg += "_Her gun bu kanallari kontrol et:_\n\n"

    msg += "*🇹🇷 Türkiye Diş Hekimliği*\n"
    tg_kanallar_tr = [
        ("Dis Hekimligi Sozlugu",       "https://t.me/DisHekimligiSozlugu"),
        ("Dis Hekimleri Toplulugu DHT", "https://t.me/+m8O7QpFBn0A5NDc0"),
    ]
    for isim, url in tg_kanallar_tr:
        msg += f"  ▸ [{isim}]({url})\n"

    msg += "\n*🌍 Uluslararası / Balkanlar*\n"
    tg_kanallar_int = [
        ("IAOMS Official",     "https://t.me/iaoms_official"),
        ("Dental Tribune",     "https://t.me/dentaltribune"),
        ("Implant Tribune",    "https://t.me/implanttribune"),
        ("Osstem Global",      "https://t.me/osstemimplant"),
        ("ITI Network",        "https://t.me/iti_dental"),
    ]
    for isim, url in tg_kanallar_int:
        msg += f"  ▸ [{isim}]({url})\n"

    msg += "\n*🦷 Oda Stomatologjike Kosova*\n"
    msg += "  ▸ [Facebook Sayfasi](https://www.facebook.com/odastomatologjike)\n"
    msg += "_Not: Oda henuz Telegram'da yok — Facebook'tan takip et._\n"

    return msg




# ══════════════════════════════════════════════════════════════════════
#  📱  TELEGRAM
# ══════════════════════════════════════════════════════════════════════

def telegram_gonder(mesaj, etiket=""):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    for parca in [mesaj[i:i+4000] for i in range(0, len(mesaj), 4000)]:
        try:
            r = requests.post(url,
                              json={"chat_id": TELEGRAM_CHAT_ID, "text": parca,
                                    "parse_mode": "Markdown",
                                    "disable_web_page_preview": False},
                              timeout=15)
            r.raise_for_status()
            time.sleep(0.5)
        except Exception as e:
            print(f"❌ Telegram [{etiket}]: {e}")
            try: print(f"   {r.text[:200]}")
            except: pass
            return False
    print(f"✅ Gönderildi: {etiket}")
    return True


# ══════════════════════════════════════════════════════════════════════
#  ▶️  ANA PROGRAM
# ══════════════════════════════════════════════════════════════════════

def main():
    print("=" * 55)
    print("  FonRadar + KursRadar + DiştakipRadar v3")
    print(f"  {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print("=" * 55)

    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Token eksik! GitHub Secrets'a TELEGRAM_TOKEN ve TELEGRAM_CHAT_ID ekle.")
        exit(1)

    hafta_ici = date.today().weekday() < 5  # 0=Pzt…4=Cum

    # 1. ETF Sinyalleri — yalnızca hafta içi
    if hafta_ici:
        print("\n📊 ETF analiz ediliyor...")
        etf_sonuclari = []
        for sembol in ETF_PORTFOY:
            print(f"  {sembol}...", end=" ", flush=True)
            fiyatlar = etf_veri_cek(sembol)
            time.sleep(0.7)
            if fiyatlar:
                a = etf_analiz(sembol, fiyatlar)
                etf_sonuclari.append(a)
                print(f"{a['gunluk']:+.2f}% → {a['sinyal']}")
            else:
                print("veri yok")
        if etf_sonuclari:
            telegram_gonder(etf_raporu(etf_sonuclari), "ETF Raporu")
        else:
            telegram_gonder("⚠️ ETF verileri alınamadı.", "ETF Hata")
    else:
        print("\n📅 Hafta sonu — ETF raporu atlandı")

    # 2. Diş Deposu Takibi — her gün
    print("\n🦷 Diş depoları taranıyor (14 firma)...")
    telegram_gonder(dis_deposu_raporu(), "Diş Deposu")

    # 3. Kurs Bildirimi — her gün
    print("\n🎓 Kurslar aranıyor...")
    telegram_gonder(kurs_raporu(), "Kurslar")

    # 4. Kosova Haberleri + Oda Stomatologjike — her gün
    print("\n📰 Haberler taranıyor...")
    telegram_gonder(haber_raporu(), "Haberler")

    # 5. Instagram Takip Hatırlatması — her gün
    print("\n📱 Instagram hatırlatması gönderiliyor...")
    telegram_gonder(instagram_hatirlatma(), "Instagram")

    print("\n✅ Tüm görevler tamamlandı.")


if __name__ == "__main__":
    main()
