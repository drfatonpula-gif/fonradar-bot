"""
FonRadar Tam Bot — PythonAnywhere Edition
/ara komutuyla PDF arama dahil
"""
 
import os, time, threading, statistics, requests, schedule
import xml.etree.ElementTree as ET
from datetime import datetime, date, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
 
TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
GITHUB_USER      = "drfatonpula-gif"
GITHUB_REPO      = "fonradar-bot"
 
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
HEADERS = {"User-Agent": "Mozilla/5.0"}
GITHUB_HEADERS = {"User-Agent": "Mozilla/5.0", "Authorization": f"token {GITHUB_TOKEN}"}
YAHOO   = "https://query1.finance.yahoo.com/v8/finance/chart"
 
HATIRLATMALAR = []
HATIRLATMA_ID = 0
PDF_INDEX     = {}
PDF_INDEX_TARİH = None
 
ETF_PORTFOY = {
    "IGLN.L":"🟡 Altin", "GDX":"🟡 Altin Mad.",
    "IWDA.L":"📈 Global", "EXW1.DE":"📈 Avrupa",
    "IUIT.L":"📈 Teknoloji", "IEAG.L":"💵 Tahvil", "IDTL.L":"💵 ABD",
}
 
# ── ETF ──────────────────────────────────────────────────────────────
def etf_veri(s):
    try:
        r = requests.get(f"{YAHOO}/{s}", params={"range":"30d","interval":"1d"},
                         headers=HEADERS, timeout=15)
        c = r.json()["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        return [x for x in c if x is not None] or None
    except: return None
 
def rsi(f, p=14):
    if len(f)<p+1: return 50.0
    d=[f[i]-f[i-1] for i in range(1,len(f))]
    k=statistics.mean([x for x in d[-p:] if x>0] or [0.001])
    y=statistics.mean([-x for x in d[-p:] if x<0] or [0.001])
    return round(100-100/(1+k/y),1)
 
def etf_analiz(s,f):
    son=f[-1]; dun=f[-2]
    f5=f[-6] if len(f)>=6 else f[0]
    gun=(son-dun)/dun*100; t5=(son-f5)/f5*100
    r=rsi(f); ma5=statistics.mean(f[-5:])
    ma20=statistics.mean(f[-20:]) if len(f)>=20 else statistics.mean(f)
    dg=[abs((f[i]-f[i-1])/f[i-1]*100) for i in range(1,len(f))]
    vol=statistics.stdev(dg[-10:]) if len(dg)>=3 else 0
    p=0
    if 35<=r<=65: p+=1.5
    elif r<30: p+=0.8
    if t5>0 and gun>0: p+=2
    elif t5>0: p+=0.8
    if son>ma5 and son>ma20: p+=2
    elif son>ma5: p+=0.8
    if vol<1: p+=1
    elif vol<2: p+=0.5
    g=min(int(p/7*100),100)
    if gun>=0.3 and t5>=1 and g>=60: sinyal="🟢 AL"
    elif gun<=-0.3 and t5<=-1 and g<40: sinyal="🔴 SAT"
    elif g>=68: sinyal="🟢 AL"
    elif g<=32: sinyal="🔴 SAT"
    else: sinyal="🟡 BEKLE"
    return {"s":s,"gun":round(gun,2),"g":g,"sinyal":sinyal}
 
def etf_mesaj():
    msg=f"📊 *ETF RAPORU*\n🗓 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
    al=[]; sat=[]; bekle=[]
    for s in ETF_PORTFOY:
        f=etf_veri(s); time.sleep(0.5)
        if f and len(f)>=5:
            a=etf_analiz(s,f)
            if "AL" in a["sinyal"]: al.append(a)
            elif "SAT" in a["sinyal"]: sat.append(a)
            else: bekle.append(a)
    if al:
        msg+=f"🟢 *AL* ({len(al)})\n"
        for a in sorted(al,key=lambda x:x["g"],reverse=True):
            msg+=f"  `{a['s']}` {a['gun']:+.2f}% | {a['g']}%\n"
    if sat:
        msg+=f"\n🔴 *SAT* ({len(sat)})\n"
        for a in sat: msg+=f"  `{a['s']}` {a['gun']:+.2f}%\n"
    if bekle:
        msg+=f"\n🟡 *BEKLE:* "+" ".join(f"`{a['s']}`" for a in bekle)
    return msg
 
# ── Haber ────────────────────────────────────────────────────────────
def haber_mesaj():
    yil=datetime.now().year
    msg=f"📰 *HABERLER*\n🗓 {datetime.now().strftime('%d.%m.%Y')}\n\n"
    for isim,sorgu in [
        ("Koha.net", f"koha.net dental stomatolog Kosovo {yil}"),
        ("Gazeta Blic", f"gazetablic dental stomatolog Kosovo {yil}"),
    ]:
        try:
            r=requests.get("https://api.duckduckgo.com/",
                params={"q":sorgu,"format":"json","no_redirect":1,"no_html":1},
                headers=HEADERS, timeout=12)
            data=r.json()
            sonuc=[]
            if data.get("AbstractURL"): sonuc.append({"b":data.get("Heading","")[:60],"u":data["AbstractURL"]})
            for item in data.get("RelatedTopics",[])[:2]:
                if isinstance(item,dict) and item.get("FirstURL"):
                    sonuc.append({"b":item.get("Text","")[:60],"u":item["FirstURL"]})
            if sonuc:
                msg+=f"*{isim}*\n"
                for s in sonuc[:2]: msg+=f"  [{s['b']}]({s['u']})\n"
                msg+="\n"
        except: pass
        time.sleep(0.5)
    msg+="[Oda Stomatologjike](https://www.facebook.com/odastomatologjike)"
    return msg
 
# ── PDF Arama ────────────────────────────────────────────────────────
def pdf_index_guncelle():
    global PDF_INDEX, PDF_INDEX_TARİH
    print("📄 PDF index güncelleniyor...")
    url=f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/pdfs"
    try:
        r=requests.get(url, headers=GITHUB_HEADERS, timeout=15)
        if r.status_code==404:
            print("  pdfs/ klasörü yok")
            return 0
        dosyalar=[f for f in r.json() if isinstance(f,dict) and f.get("name","").lower().endswith((".pdf",".docx",".doc"))]
    except: return 0
 
   
   yeni={}
    for d in dosyalar:
        if d.get("size", 0) > 5000000:
            print(f"  ⏭ {d['name']} atlandı (cok buyuk)")
            continue
        print(f"  📖 {d['name']} okunuyor...")
        try:
            rb=requests.get(d["download_url"], headers=GITHUB_HEADERS, timeout=30)
            import tempfile, re
            with tempfile.NamedTemporaryFile(suffix=".pdf",delete=False) as tmp:
                tmp.write(rb.content); tmp_path=tmp.name
            try:
                if d["name"].lower().endswith((".docx", ".doc")):
                    # Word dosyası
                    from docx import Document
                    doc = Document(tmp_path)
                    metin = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
                    sayfalar = [{"n": 1, "t": metin}]
                else:
                    # PDF
                    from pdfminer.high_level import extract_pages
                    from pdfminer.layout import LTTextContainer
                    sayfalar=[]; no=0
                    for pg in extract_pages(tmp_path):
                        no+=1; t=""
                        for el in pg:
                            if isinstance(el,LTTextContainer): t+=el.get_text()
                        sayfalar.append({"n":no,"t":t.strip()})
            except:
                sayfalar=[{"n":1,"t":""}]
            os.unlink(tmp_path)
            yeni[d["name"]]=sayfalar
            print(f"  ✅ {len(sayfalar)} sayfa")
        except Exception as e:
            print(f"  ❌ {e}")
        time.sleep(1)
 
    PDF_INDEX=yeni
    PDF_INDEX_TARİH=datetime.now().strftime("%d.%m.%Y %H:%M")
    return len(PDF_INDEX)
 
def pdf_ara_yap(sorgu):
    global PDF_INDEX
    if not PDF_INDEX:
        adet=pdf_index_guncelle()
        if adet==0:
            return (f"❌ PDF bulunamadı.\n\n"
                    f"GitHub'da `pdfs/` klasörü oluştur ve PDF yükle:\n"
                    f"github.com/{GITHUB_USER}/{GITHUB_REPO}")
    ql=sorgu.lower(); sonuclar=[]
    for dosya,sayfalar in PDF_INDEX.items():
        for s in sayfalar:
            idx=s["t"].lower().find(ql)
            if idx!=-1:
                b=max(0,idx-100); e=min(len(s["t"]),idx+200)
                sonuclar.append({"d":dosya.replace(".pdf",""),"s":s["n"],"p":s["t"][b:e].strip()})
    if not sonuclar:
        return f"🔍 *'{sorgu}'* bulunamadı."
    msg=f"🔍 *'{sorgu}'* — {len(sonuclar)} sonuç\n_{PDF_INDEX_TARİH}_\n\n"
    for s in sonuclar[:6]:
        msg+=f"📄 *{s['d']}* — Sayfa {s['s']}\n_{s['p'][:150]}_\n\n"
    if len(sonuclar)>6: msg+=f"_...{len(sonuclar)-6} sonuç daha_"
    return msg
 
# ── Telegram ────────────────────────────────────────────────────────
def tg_gonder(metin, chat_id):
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id":chat_id,"text":metin,"parse_mode":"Markdown"}, timeout=15)
    except Exception as e: print(f"TG hata: {e}")
 
def hatirlatma_kontrol():
    global HATIRLATMALAR
    simdi=datetime.now().strftime("%H:%M"); bugun=date.today().strftime("%Y-%m-%d")
    gonder=[h for h in HATIRLATMALAR if h["t"]==bugun and h["s"]==simdi]
    HATIRLATMALAR=[h for h in HATIRLATMALAR if not(h["t"]==bugun and h["s"]==simdi)]
    for h in gonder:
        tg_gonder(f"⏰ *HATIRLATMA*\n\n{h['m']}\n\n_({h['s']})_", h["c"])
 
def gunluk_rapor():
    if not TELEGRAM_CHAT_ID: return
    if date.today().weekday()<5:
        tg_gonder(etf_mesaj(), TELEGRAM_CHAT_ID); time.sleep(2)
    tg_gonder(haber_mesaj(), TELEGRAM_CHAT_ID)
 
def zamanlayici():
    schedule.every().day.at("07:00").do(gunluk_rapor)
    schedule.every().minute.do(hatirlatma_kontrol)
    while True:
        schedule.run_pending(); time.sleep(30)
 
# ── Komutlar ─────────────────────────────────────────────────────────
async def cmd_start(u,c): await u.message.reply_text("👋 *FonRadar Bot!*\n\n/yardim yaz.",parse_mode="Markdown")
 
async def cmd_yardim(u,c):
    await u.message.reply_text(
        "🤖 *Komutlar*\n\n"
        "`/ara implant` — PDF'lerde ara\n"
        "`/pdfler` — yüklü PDF listesi\n"
        "`/pdfguncelle` — PDF index yenile\n\n"
        "`/hatirlatma 14:30 metin`\n"
        "`/yarin 09:00 metin`\n"
        "`/liste` — hatırlatmalar\n"
        "`/sil 2`\n\n"
        "`/etf` — ETF sinyalleri\n"
        "`/haberler` — haberler\n"
        "`/rapor` — her ikisi",
        parse_mode="Markdown")
 
async def cmd_ara(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if not c.args:
        await u.message.reply_text("Kullanım: `/ara implant`", parse_mode="Markdown"); return
    sorgu=" ".join(c.args)
    await u.message.reply_text(f"🔍 *'{sorgu}'* aranıyor...", parse_mode="Markdown")
    sonuc=pdf_ara_yap(sorgu)
    await u.message.reply_text(sonuc, parse_mode="Markdown")
 
async def cmd_pdfler(u,c):
    if not PDF_INDEX:
        await u.message.reply_text("Henüz index yok. /pdfguncelle yaz."); return
    msg=f"📄 *PDF Listesi* ({len(PDF_INDEX)} dosya)\n\n"
    for d,s in PDF_INDEX.items(): msg+=f"• {d} — {len(s)} sayfa\n"
    await u.message.reply_text(msg, parse_mode="Markdown")
 
async def cmd_pdfguncelle(u,c):
    await u.message.reply_text("⏳ PDF'ler indexleniyor...")
    adet=pdf_index_guncelle()
    await u.message.reply_text(f"✅ {adet} PDF indexlendi.")
 
async def cmd_hatirlatma(u: Update, c: ContextTypes.DEFAULT_TYPE):
    global HATIRLATMALAR, HATIRLATMA_ID
    cid=u.effective_chat.id; args=c.args
    if len(args)<2:
        await u.message.reply_text("Kullanım: `/hatirlatma 14:30 metin`",parse_mode="Markdown"); return
    saat=args[0]; metin=" ".join(args[1:])
    try: datetime.strptime(saat,"%H:%M")
    except:
        await u.message.reply_text("Saat formatı: `14:30`",parse_mode="Markdown"); return
    bugun=date.today().strftime("%Y-%m-%d"); simdi=datetime.now().strftime("%H:%M")
    tarih=bugun if saat>simdi else (date.today()+timedelta(days=1)).strftime("%Y-%m-%d")
    HATIRLATMA_ID+=1
    HATIRLATMALAR.append({"id":HATIRLATMA_ID,"s":saat,"t":tarih,"m":metin,"c":cid})
    gun="Bugün" if tarih==bugun else "Yarın"
    await u.message.reply_text(f"✅ *{gun} {saat}*\n{metin}",parse_mode="Markdown")
 
async def cmd_yarin(u: Update, c: ContextTypes.DEFAULT_TYPE):
    global HATIRLATMALAR, HATIRLATMA_ID
    cid=u.effective_chat.id; args=c.args
    if len(args)<2:
        await u.message.reply_text("Kullanım: `/yarin 09:00 metin`",parse_mode="Markdown"); return
    saat=args[0]; metin=" ".join(args[1:])
    try: datetime.strptime(saat,"%H:%M")
    except:
        await u.message.reply_text("Saat formatı: `09:00`",parse_mode="Markdown"); return
    yarin=(date.today()+timedelta(days=1)).strftime("%Y-%m-%d")
    HATIRLATMA_ID+=1
    HATIRLATMALAR.append({"id":HATIRLATMA_ID,"s":saat,"t":yarin,"m":metin,"c":cid})
    await u.message.reply_text(f"✅ *Yarın {saat}*\n{metin}",parse_mode="Markdown")
 
async def cmd_liste(u: Update, c: ContextTypes.DEFAULT_TYPE):
    cid=u.effective_chat.id; mine=[h for h in HATIRLATMALAR if h["c"]==cid]
    if not mine:
        await u.message.reply_text("Kayıtlı hatırlatma yok."); return
    bugun=date.today().strftime("%Y-%m-%d"); yarin=(date.today()+timedelta(days=1)).strftime("%Y-%m-%d")
    msg="📋 *Hatırlatmalar:*\n\n"
    for h in mine:
        gun="Bugün" if h["t"]==bugun else ("Yarın" if h["t"]==yarin else h["t"])
        msg+=f"*{h['id']}.* {gun} {h['s']} — {h['m']}\n"
    await u.message.reply_text(msg,parse_mode="Markdown")
 
async def cmd_sil(u: Update, c: ContextTypes.DEFAULT_TYPE):
    global HATIRLATMALAR; cid=u.effective_chat.id
    if not c.args:
        await u.message.reply_text("Kullanım: `/sil 1`",parse_mode="Markdown"); return
    try: hid=int(c.args[0])
    except:
        await u.message.reply_text("Geçerli numara gir."); return
    once=len(HATIRLATMALAR)
    HATIRLATMALAR=[h for h in HATIRLATMALAR if not(h["id"]==hid and h["c"]==cid)]
    await u.message.reply_text("✅ Silindi." if len(HATIRLATMALAR)<once else "Bulunamadı.")
 
async def cmd_iptal(u,c):
    global HATIRLATMALAR; cid=u.effective_chat.id
    sayi=len([h for h in HATIRLATMALAR if h["c"]==cid])
    HATIRLATMALAR=[h for h in HATIRLATMALAR if h["c"]!=cid]
    await u.message.reply_text(f"✅ {sayi} hatırlatma silindi.")
 
async def cmd_etf(u,c):
    await u.message.reply_text("⏳ ETF çekiliyor...")
    await u.message.reply_text(etf_mesaj(),parse_mode="Markdown")
 
async def cmd_haberler(u,c):
    await u.message.reply_text("⏳ Haberler yükleniyor...")
    await u.message.reply_text(haber_mesaj(),parse_mode="Markdown")
 
async def cmd_rapor(u,c):
    await u.message.reply_text("⏳ Hazırlanıyor...")
    await u.message.reply_text(etf_mesaj(),parse_mode="Markdown")
    await u.message.reply_text(haber_mesaj(),parse_mode="Markdown")
 
# ── Ana program ──────────────────────────────────────────────────────
def main():
    print("="*45)
    print("  FonRadar Bot — PythonAnywhere")
    print(f"  {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print("="*45)
 
    if not TELEGRAM_TOKEN:
        print("TELEGRAM_TOKEN eksik!")
        return
 
    # PDF'leri başlangıçta indexle
    threading.Thread(target=pdf_index_guncelle, daemon=True).start()
 
    # Zamanlayıcı
    threading.Thread(target=zamanlayici, daemon=True).start()
 
    # Bot
    app=Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start",       cmd_start))
    app.add_handler(CommandHandler("yardim",      cmd_yardim))
    app.add_handler(CommandHandler("ara",         cmd_ara))
    app.add_handler(CommandHandler("pdfler",      cmd_pdfler))
    app.add_handler(CommandHandler("pdfguncelle", cmd_pdfguncelle))
    app.add_handler(CommandHandler("hatirlatma",  cmd_hatirlatma))
    app.add_handler(CommandHandler("yarin",       cmd_yarin))
    app.add_handler(CommandHandler("liste",       cmd_liste))
    app.add_handler(CommandHandler("sil",         cmd_sil))
    app.add_handler(CommandHandler("iptal",       cmd_iptal))
    app.add_handler(CommandHandler("etf",         cmd_etf))
    app.add_handler(CommandHandler("haberler",    cmd_haberler))
    app.add_handler(CommandHandler("rapor",       cmd_rapor))
 
    print("Bot dinleniyor...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)
 
if __name__=="__main__":
    main()
