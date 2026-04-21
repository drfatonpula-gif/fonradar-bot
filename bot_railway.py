"""
FonRadar Tam Bot — Railway Edition
7/24 çalışır, Telegram'dan komut alır.
 
Komutlar:
  /hatirlatma 14:30 Nobel toplantisi
  /yarin 09:00 Bora Dental ziyareti
  /liste
  /sil 1
  /iptal
  /rapor
  /etf
  /haberler
  /yardim
"""
 
import os
import time
import threading
import statistics
import requests
import schedule
import xml.etree.ElementTree as ET
from datetime import datetime, date, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
 
TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
HEADERS = {"User-Agent": "Mozilla/5.0"}
YAHOO   = "https://query1.finance.yahoo.com/v8/finance/chart"
 
HATIRLATMALAR = []
HATIRLATMA_ID = 0
 
ETF_PORTFOY = {
    "IGLN.L": "🟡 Altin", "GDX": "🟡 Altin Mad.",
    "IWDA.L": "📈 Global", "EXW1.DE": "📈 Avrupa",
    "IUIT.L": "📈 Teknoloji", "IEAG.L": "💵 Tahvil", "IDTL.L": "💵 ABD Tahvil",
}
 
def etf_veri(sembol):
    try:
        r = requests.get(f"{YAHOO}/{sembol}", params={"range":"30d","interval":"1d"},
                         headers=HEADERS, timeout=15)
        c = r.json()["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        return [x for x in c if x is not None] or None
    except:
        return None
 
def rsi_hesapla(f, p=14):
    if len(f) < p+1: return 50.0
    d = [f[i]-f[i-1] for i in range(1,len(f))]
    k = statistics.mean([x for x in d[-p:] if x>0] or [0.001])
    y = statistics.mean([-x for x in d[-p:] if x<0] or [0.001])
    return round(100-100/(1+k/y), 1)
 
def etf_analiz(s, f):
    son=f[-1]; dun=f[-2]
    f5=f[-6] if len(f)>=6 else f[0]
    gun=(son-dun)/dun*100; t5=(son-f5)/f5*100
    r=rsi_hesapla(f)
    ma5=statistics.mean(f[-5:])
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
    return {"s":s, "gun":round(gun,2), "rsi":r, "g":g, "sinyal":sinyal}
 
def etf_mesaj():
    msg = f"📊 *ETF SİNYAL RAPORU*\n🗓 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
    al=[]; sat=[]; bekle=[]
    for sembol in ETF_PORTFOY:
        f = etf_veri(sembol)
        time.sleep(0.5)
        if f and len(f)>=5:
            a = etf_analiz(sembol, f)
            if "AL" in a["sinyal"]: al.append(a)
            elif "SAT" in a["sinyal"]: sat.append(a)
            else: bekle.append(a)
    if al:
        msg += f"🟢 *AL* ({len(al)})\n"
        for a in sorted(al, key=lambda x: x["g"], reverse=True):
            msg += f"  `{a['s']}` {a['gun']:+.2f}% | {a['g']}% guven\n"
    if sat:
        msg += f"\n🔴 *SAT* ({len(sat)})\n"
        for a in sat:
            msg += f"  `{a['s']}` {a['gun']:+.2f}%\n"
    if bekle:
        msg += f"\n🟡 *BEKLE:* " + " ".join(f"`{a['s']}`" for a in bekle)
    if not al and not sat and not bekle:
        msg += "_Veri alinamadi._"
    return msg
 
def haber_mesaj():
    msg = f"📰 *KOSOVA HABERLERİ*\n🗓 {datetime.now().strftime('%d.%m.%Y')}\n\n"
    kaynaklar = [
        ("Koha.net",     "https://www.koha.net/feed/",
         ["dental","stomatolog","shendet","klinik","implant","kurs"]),
        ("Gazeta Blic",  "https://gazetablic.com/feed/",
         ["dental","stomatolog","shendet","klinik","kurs"]),
    ]
    for isim, url, anahtar in kaynaklar:
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            root = ET.fromstring(r.content)
            sonuc = []
            for item in root.findall(".//item")[:15]:
                baslik = item.findtext("title") or ""
                link   = item.findtext("link") or url
                if any(k.lower() in baslik.lower() for k in anahtar):
                    sonuc.append({"b": baslik[:70], "u": link})
            if sonuc:
                msg += f"*{isim}*\n"
                for s in sonuc[:3]:
                    msg += f"  [{s['b']}]({s['u']})\n"
                msg += "\n"
        except:
            pass
        time.sleep(0.5)
    msg += "[Oda Stomatologjike](https://www.facebook.com/odastomatologjike)\n"
    return msg
 
def telegram_gonder(metin, chat_id):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={
            "chat_id": chat_id,
            "text": metin,
            "parse_mode": "Markdown"
        }, timeout=15)
    except Exception as e:
        print(f"Telegram hata: {e}")
 
def hatirlatma_kontrol():
    global HATIRLATMALAR
    simdi_saat = datetime.now().strftime("%H:%M")
    bugun      = date.today().strftime("%Y-%m-%d")
    gonder = [h for h in HATIRLATMALAR
              if h["tarih"] == bugun and h["saat"] == simdi_saat]
    HATIRLATMALAR = [h for h in HATIRLATMALAR
                     if not (h["tarih"] == bugun and h["saat"] == simdi_saat)]
    for h in gonder:
        telegram_gonder(
            f"⏰ *HATIRLATMA*\n\n{h['metin']}\n\n_({h['saat']} icin ayarlanmisti)_",
            h["chat_id"]
        )
 
def gunluk_rapor():
    if not TELEGRAM_CHAT_ID: return
    print(f"📊 Gunluk rapor — {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    if date.today().weekday() < 5:
        telegram_gonder(etf_mesaj(), TELEGRAM_CHAT_ID)
        time.sleep(2)
    telegram_gonder(haber_mesaj(), TELEGRAM_CHAT_ID)
 
def zamanlayici():
    schedule.every().day.at("07:00").do(gunluk_rapor)
    schedule.every().minute.do(hatirlatma_kontrol)
    print("Zamanlayici basladi")
    while True:
        schedule.run_pending()
        time.sleep(30)
 
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 *FonRadar Bot'a hos geldin!*\n\n/yardim yaz.",
        parse_mode="Markdown"
    )
 
async def cmd_yardim(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = (
        "🤖 *Komutlar*\n\n"
        "`/hatirlatma 14:30 Nobel toplantisi`\n"
        "`/yarin 09:00 Bora Dental ziyareti`\n"
        "`/liste` — hatirlatmalari goster\n"
        "`/sil 2` — 2 numarayi sil\n"
        "`/iptal` — hepsini sil\n\n"
        "`/rapor` — ETF + haberler\n"
        "`/etf` — sadece ETF\n"
        "`/haberler` — sadece haberler"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")
 
async def cmd_hatirlatma(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    global HATIRLATMALAR, HATIRLATMA_ID
    chat_id = update.effective_chat.id
    args = ctx.args
    if len(args) < 2:
        await update.message.reply_text("Kullanim: `/hatirlatma 14:30 metin`", parse_mode="Markdown")
        return
    saat = args[0]; metin = " ".join(args[1:])
    try: datetime.strptime(saat, "%H:%M")
    except:
        await update.message.reply_text("Saat formati yanlis. Ornek: `14:30`", parse_mode="Markdown")
        return
    bugun = date.today().strftime("%Y-%m-%d")
    simdi = datetime.now().strftime("%H:%M")
    tarih = bugun if saat > simdi else (date.today()+timedelta(days=1)).strftime("%Y-%m-%d")
    HATIRLATMA_ID += 1
    HATIRLATMALAR.append({"id":HATIRLATMA_ID,"saat":saat,"tarih":tarih,"metin":metin,"chat_id":chat_id})
    gun = "Bugun" if tarih == bugun else "Yarin"
    await update.message.reply_text(
        f"✅ *{gun} {saat}*\n{metin}", parse_mode="Markdown"
    )
 
async def cmd_yarin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    global HATIRLATMALAR, HATIRLATMA_ID
    chat_id = update.effective_chat.id
    args = ctx.args
    if len(args) < 2:
        await update.message.reply_text("Kullanim: `/yarin 09:00 metin`", parse_mode="Markdown")
        return
    saat = args[0]; metin = " ".join(args[1:])
    try: datetime.strptime(saat, "%H:%M")
    except:
        await update.message.reply_text("Saat formati yanlis. Ornek: `09:00`", parse_mode="Markdown")
        return
    yarin = (date.today()+timedelta(days=1)).strftime("%Y-%m-%d")
    HATIRLATMA_ID += 1
    HATIRLATMALAR.append({"id":HATIRLATMA_ID,"saat":saat,"tarih":yarin,"metin":metin,"chat_id":chat_id})
    await update.message.reply_text(f"✅ *Yarin {saat}*\n{metin}", parse_mode="Markdown")
 
async def cmd_liste(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    mine = [h for h in HATIRLATMALAR if h["chat_id"] == chat_id]
    if not mine:
        await update.message.reply_text("Kayitli hatirlatma yok.")
        return
    bugun = date.today().strftime("%Y-%m-%d")
    yarin = (date.today()+timedelta(days=1)).strftime("%Y-%m-%d")
    msg = "📋 *Hatirlatmalar:*\n\n"
    for h in mine:
        gun = "Bugun" if h["tarih"]==bugun else ("Yarin" if h["tarih"]==yarin else h["tarih"])
        msg += f"*{h['id']}.* {gun} {h['saat']} — {h['metin']}\n"
    msg += "\n_Silmek icin: /sil [numara]_"
    await update.message.reply_text(msg, parse_mode="Markdown")
 
async def cmd_sil(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    global HATIRLATMALAR
    chat_id = update.effective_chat.id
    if not ctx.args:
        await update.message.reply_text("Kullanim: `/sil 1`", parse_mode="Markdown")
        return
    try: hedef = int(ctx.args[0])
    except:
        await update.message.reply_text("Gecerli bir numara gir.")
        return
    onceki = len(HATIRLATMALAR)
    HATIRLATMALAR = [h for h in HATIRLATMALAR
                     if not (h["id"]==hedef and h["chat_id"]==chat_id)]
    if len(HATIRLATMALAR) < onceki:
        await update.message.reply_text(f"✅ {hedef} numarali hatirlatma silindi.")
    else:
        await update.message.reply_text("Bu numara bulunamadi.")
 
async def cmd_iptal(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    global HATIRLATMALAR
    chat_id = update.effective_chat.id
    sayi = len([h for h in HATIRLATMALAR if h["chat_id"]==chat_id])
    HATIRLATMALAR = [h for h in HATIRLATMALAR if h["chat_id"]!=chat_id]
    await update.message.reply_text(f"✅ {sayi} hatirlatma silindi.")
 
async def cmd_rapor(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hazirlaniyor...")
    await update.message.reply_text(etf_mesaj(), parse_mode="Markdown")
    await update.message.reply_text(haber_mesaj(), parse_mode="Markdown")
 
async def cmd_etf(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ETF verileri cekiliyor...")
    await update.message.reply_text(etf_mesaj(), parse_mode="Markdown")
 
async def cmd_haberler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Haberler yukleniyor...")
    await update.message.reply_text(haber_mesaj(), parse_mode="Markdown")
 
def main():
    print("=" * 45)
    print("  FonRadar Tam Bot — Railway Edition")
    print(f"  {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print("=" * 45)
    if not TELEGRAM_TOKEN:
        print("TELEGRAM_TOKEN eksik!")
        return
    t = threading.Thread(target=zamanlayici, daemon=True)
    t.start()
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start",      cmd_start))
    app.add_handler(CommandHandler("yardim",     cmd_yardim))
    app.add_handler(CommandHandler("hatirlatma", cmd_hatirlatma))
    app.add_handler(CommandHandler("yarin",      cmd_yarin))
    app.add_handler(CommandHandler("liste",      cmd_liste))
    app.add_handler(CommandHandler("sil",        cmd_sil))
    app.add_handler(CommandHandler("iptal",      cmd_iptal))
    app.add_handler(CommandHandler("rapor",      cmd_rapor))
    app.add_handler(CommandHandler("etf",        cmd_etf))
    app.add_handler(CommandHandler("haberler",   cmd_haberler))
    print("Bot dinleniyor...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)
 
if __name__ == "__main__":
    main()
