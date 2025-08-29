
from flask import Flask, request, jsonify
import os, json, csv, time, requests
from apscheduler.schedulers.background import BackgroundScheduler

BOT_TOKEN = os.environ.get("BOT_TOKEN", "7597035485:AAF00NyMxzCNaFjRz2r5MliaV9ndSdqJ9Lg")
ADMIN_ID = os.environ.get("ADMIN_ID", "5130562279")
VIP_LINK = "https://t.me/VIP_CryptoN1_bot"
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = Flask(__name__)
PENDING_FILE = "pending.json"
CSV_FILE = "payments_log.csv"

USER_LANG = {}
MESSAGES = {
    "start": {"ar":"مرحبًا 👋! اختر طريقة الدفع للحصول على اشتراك VIP:",
              "en":"Hello 👋! Please choose your payment method to get VIP access:",
              "fr":"Bonjour 👋! Veuillez choisir votre méthode de paiement pour accéder au VIP :"},
    "pay_instructions": {
        "PayPal": {"ar":"💳 أرسل 200$ إلى: mimoucanadien01@gmail.com ثم أرسل إثبات الدفع هنا.",
                   "en":"💳 Send $200 to: mimoucanadien01@gmail.com then send your proof of payment here.",
                   "fr":"💳 Envoyez 200$ à : mimoucanadien01@gmail.com puis envoyez votre preuve de paiement ici."},
        "BaridiMob":{"ar":"🏦 أرسل 48000 DA إلى: 00799999001806537421 ثم أرسل إثبات الدفع هنا.",
                     "en":"🏦 Send 48000 DA to: 00799999001806537421 then send your proof of payment here.",
                     "fr":"🏦 Envoyez 48000 DA à : 00799999001806537421 puis envoyez votre preuve de paiement ici."},
        "USDT":{"ar":"💰 أرسل 200 USDT إلى: 0x1aaa53596e4a3fc411bdf5c8c9c315b2253bcbda أو 0x4ec85ef2dca621ed2cdd0dbed7a9ee2d5d688f20 ثم أرسل الإثبات هنا.",
                "en":"💰 Send 200 USDT to: 0x1aaa53596e4a3fc411bdf5c8c9c315b2253bcbda or 0x4ec85ef2dca621ed2cdd0dbed7a9ee2d5d688f20, then send your proof here.",
                "fr":"💰 Envoyez 200 USDT à : 0x1aaa53596e4a3fc411bdf5c8c9c315b2253bcbda ou 0x4ec85ef2dca621ed2cdd0dbed7a9ee2d5d688f20, puis envoyez la preuve ici."}
    },
    "proof_received":{"ar":"✅ استلمنا إثبات الدفع الخاص بك وسيتم مراجعته من قبل الأدمن.",
                      "en":"✅ We have received your payment proof and it will be reviewed by the admin.",
                      "fr":"✅ Nous avons reçu votre preuve de paiement et elle sera vérifiée par l’administrateur."},
    "confirm":{"ar":"🎉 تم تأكيد الدفع! إليك رابط قناة VIP:\n{VIP_LINK}",
               "en":"🎉 Payment confirmed! Here is the VIP channel link:\n{VIP_LINK}",
               "fr":"🎉 Paiement confirmé ! Voici le lien du canal VIP:\n{VIP_LINK}"}
}

def init_files():
    if not os.path.exists(PENDING_FILE):
        with open(PENDING_FILE,"w",encoding="utf-8") as f: json.dump({},f)
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE,"w",newline="",encoding="utf-8") as f:
            csv.writer(f).writerow(["timestamp","user_id","username","name","method","admin_id"])
init_files()

def load_pending():
    with open(PENDING_FILE,"r",encoding="utf-8") as f: return json.load(f)
def save_pending(data):
    with open(PENDING_FILE,"w",encoding="utf-8") as f: json.dump(data,f,ensure_ascii=False,indent=2)
def log_payment(row):
    with open(CSV_FILE,"a",newline="",encoding="utf-8") as f: csv.writer(f).writerow(row)

def api_post(method,payload):
    return requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/{method}",json=payload,timeout=15).json()
def send_message(chat_id,text,reply_markup=None):
    payload={"chat_id":chat_id,"text":text,"parse_mode":"Markdown"}
    if reply_markup: payload["reply_markup"]=reply_markup
    return api_post("sendMessage",payload)

def build_keyboard(): return {"inline_keyboard":[[{"text":"💳 PayPal","callback_data":"pay:PayPal"},{"text":"💰 USDT","callback_data":"pay:USDT"}],[{"text":"🏦 BaridiMob","callback_data":"pay:BaridiMob"}]]}
def build_admin_keyboard(user_id): return {"inline_keyboard":[[{"text":"✅ Confirm","callback_data":f"admin:confirm:{user_id}"},{"text":"❌ Reject","callback_data":f"admin:reject:{user_id}"}]]}

scheduler=BackgroundScheduler()
scheduler.start()

app = Flask(__name__)
@app.route("/health")
def health(): return "OK",200
@app.route("/webhook",methods=["POST"])
def webhook():
    data=request.get_json(force=True)
    try:
        if "message" in data:
            msg=data["message"]
            chat_id=msg["chat"]["id"]
            text=msg.get("text","")
            user=msg.get("from",{})
            username=user.get("username","")
            name=(user.get("first_name") or "")+" "+(user.get("last_name") or "")
            name=name.strip()
            if text.startswith("/start"):
                USER_LANG[chat_id]="ar"
                send_message(chat_id,MESSAGES["start"]["ar"],reply_markup=build_keyboard())
                return jsonify({"ok":True})
            if text in ["💳 PayPal","💰 USDT","🏦 BaridiMob"]:
                methods={"💳 PayPal":"PayPal","💰 USDT":"USDT","🏦 BaridiMob":"BaridiMob"}
                pending=load_pending()
                pending[str(chat_id)]={"timestamp":time.time(),"method":methods[text],"username":username,"name":name}
                save_pending(pending)
                send_message(chat_id,MESSAGES["pay_instructions"][methods[text]]["ar"])
                return jsonify({"ok":True})
        return jsonify({"ok":True})
    except Exception as e:
        os.makedirs("logs",exist_ok=True)
        with open("logs/errors.log","a",encoding="utf-8") as f:
            f.write(str(e)+"\n")
        return jsonify({"ok":False,"error":str(e)}),500

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)))
