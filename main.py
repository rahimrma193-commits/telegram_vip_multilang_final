
from flask import Flask, request, jsonify
import os, json, csv, time, requests
from apscheduler.schedulers.background import BackgroundScheduler

BOT_TOKEN = os.environ.get("BOT_TOKEN", "7597035485:AAF00NyMxzCNaFjRz2r5MliaV9ndSdqJ9Lg")
ADMIN_ID = os.environ.get("ADMIN_ID", "5130562279")
VIP_LINK = os.environ.get("VIP_INVITE_LINK", "https://t.me/+4ZDFweU1PatlMjk0")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = Flask(__name__)
PENDING_FILE = "pending.json"
CSV_FILE = "payments_log.csv"

LANG = ["ar","en","fr"]  # يدعم الثلاث لغات
USER_LANG = {}  # لتخزين لغة المستخدم عند /start

MESSAGES = {
    "start": {
        "ar": "مرحبًا 👋! اختر طريقة الدفع للحصول على اشتراك VIP:",
        "en": "Hello 👋! Please choose your payment method to get VIP access:",
        "fr": "Bonjour 👋! Veuillez choisir votre méthode de paiement pour accéder au VIP :"
    },
    "pay_instructions": {
        "PayPal": {
            "ar": "💳 أرسل 200$ إلى: mimoucanadien01@gmail.com ثم أرسل إثبات الدفع هنا.",
            "en": "💳 Send $200 to: mimoucanadien01@gmail.com then send your proof of payment here.",
            "fr": "💳 Envoyez 200$ à : mimoucanadien01@gmail.com puis envoyez votre preuve de paiement ici."
        },
        "BaridiMob": {
            "ar": "🏦 أرسل 48000 DA إلى: 00799999001806537421 ثم أرسل إثبات الدفع هنا.",
            "en": "🏦 Send 48000 DA to: 00799999001806537421 then send your proof of payment here.",
            "fr": "🏦 Envoyez 48000 DA à : 00799999001806537421 puis envoyez votre preuve de paiement ici."
        },
        "USDT": {
            "ar": "💰 أرسل 200 USDT إلى: 0x1aaa53596e4a3fc411bdf5c8c9c315b2253bcbda أو 0x4ec85ef2dca621ed2cdd0dbed7a9ee2d5d688f20 ثم أرسل الإثبات هنا.",
            "en": "💰 Send 200 USDT to: 0x1aaa53596e4a3fc411bdf5c8c9c315b2253bcbda or 0x4ec85ef2dca621ed2cdd0dbed7a9ee2d5d688f20, then send your proof here.",
            "fr": "💰 Envoyez 200 USDT à : 0x1aaa53596e4a3fc411bdf5c8c9c315b2253bcbda ou 0x4ec85ef2dca621ed2cdd0dbed7a9ee2d5d688f20, puis envoyez la preuve ici."
        }
    },
    "proof_received": {
        "ar": "✅ استلمنا إثبات الدفع الخاص بك وسيتم مراجعته من قبل الأدمن.",
        "en": "✅ We have received your payment proof and it will be reviewed by the admin.",
        "fr": "✅ Nous avons reçu votre preuve de paiement et elle sera vérifiée par l’administrateur."
    },
    "admin_notify": {
        "ar": "📥 إثبات دفع جديد من: {name}\nUser ID: {user_id}\nطريقة الدفع: {method}\nالنص: {text}",
        "en": "📥 New payment proof from: {name}\nUser ID: {user_id}\nPayment method: {method}\nText: {text}",
        "fr": "📥 Nouvelle preuve de paiement de : {name}\nID utilisateur : {user_id}\nMéthode de paiement : {method}\nTexte : {text}"
    },
    "confirm": {
        "ar": "🎉 تم تأكيد الدفع! إليك رابط قناة VIP:\n{VIP_LINK}",
        "en": "🎉 Payment confirmed! Here is the VIP channel link:\n{VIP_LINK}",
        "fr": "🎉 Paiement confirmé ! Voici le lien du canal VIP:\n{VIP_LINK}"
    },
    "reject": {
        "ar": "❌ تم رفض الدفع. يرجى إعادة المحاولة.",
        "en": "❌ Payment rejected. Please try again.",
        "fr": "❌ Paiement rejeté. Veuillez réessayer."
    },
    "reminder": {
        "ar": "⏳ هل ما زلت مهتمًا بالاشتراك؟ أكمل الدفع الآن للحصول على VIP.",
        "en": "⏳ Are you still interested in subscribing? Complete your payment now to get VIP access.",
        "fr": "⏳ Êtes-vous toujours intéressé par l’abonnement ? Complétez votre paiement maintenant pour accéder au VIP."
    },
    "expired": {
        "ar": "⏰ انتهت صلاحية إثبات الدفع الخاص بك. يرجى إعادة إرسال الدفع إذا رغبت في الاشتراك.",
        "en": "⏰ Your payment proof has expired. Please resend payment if you want to subscribe.",
        "fr": "⏰ Votre preuve de paiement a expiré. Veuillez renvoyer le paiement si vous souhaitez vous abonner."
    }
}

def init_files():
    if not os.path.exists(PENDING_FILE):
        with open(PENDING_FILE,"w",encoding="utf-8") as f:
            json.dump({},f)
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE,"w",newline="",encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp","user_id","username","name","method","admin_id"])
init_files()

def load_pending():
    with open(PENDING_FILE,"r",encoding="utf-8") as f:
        return json.load(f)
def save_pending(data):
    with open(PENDING_FILE,"w",encoding="utf-8") as f:
        json.dump(data,f,ensure_ascii=False,indent=2)
def log_payment(row):
    with open(CSV_FILE,"a",newline="",encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(row)

def api_post(method,payload):
    url=f"{TELEGRAM_API}/{method}"
    return requests.post(url,json=payload,timeout=15).json()
def send_message(chat_id,text,parse_mode="Markdown",reply_markup=None):
    payload={"chat_id":chat_id,"text":text,"parse_mode":parse_mode}
    if reply_markup: payload["reply_markup"]=reply_markup
    return api_post("sendMessage",payload)

def build_keyboard():
    return {"inline_keyboard":[
        [{"text":"💳 PayPal","callback_data":"pay:PayPal"},{"text":"💰 USDT","callback_data":"pay:USDT"}],
        [{"text":"🏦 BaridiMob","callback_data":"pay:BaridiMob"}]
    ]}
def build_admin_keyboard(user_id):
    return {"inline_keyboard":[[{"text":"✅ Confirm","callback_data":f"admin:confirm:{user_id}"},{"text":"❌ Reject","callback_data":f"admin:reject:{user_id}"}]]}

scheduler=BackgroundScheduler()
def remind():
    pending=load_pending()
    now=time.time()
    changed=False
    for uid,info in list(pending.items()):
        elapsed=now-info.get("timestamp",now)
        lang=info.get("lang","ar")
        if elapsed>=72*3600: pending.pop(uid,None); changed=True
        elif elapsed>=24*3600 and not info.get("reminded",False):
            send_message(uid,MESSAGES["reminder"][lang])
            info["reminded"]=True; changed=True
    if changed: save_pending(pending)
scheduler.add_job(remind,"interval",hours=12)
scheduler.start()

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
            # تحديد اللغة عند /start
            if text.startswith("/start"):
                lang="ar"
                if "en" in text: lang="en"
                elif "fr" in text: lang="fr"
                USER_LANG[chat_id]=lang
                send_message(chat_id,MESSAGES["start"][lang],reply_markup=build_keyboard())
                return jsonify({"ok":True})
            # تحديد طريقة الدفع
            if text in ["💳 PayPal","💰 USDT","🏦 BaridiMob"]:
                methods={"💳 PayPal":"PayPal","💰 USDT":"USDT","🏦 BaridiMob":"BaridiMob"}
                pending=load_pending()
                lang=USER_LANG.get(chat_id,"ar")
                pending[str(chat_id)]={"timestamp":time.time(),"method":methods[text],"username":username,"name":name,"reminded":False,"lang":lang}
                save_pending(pending)
                send_message(chat_id,MESSAGES["pay_instructions"][methods[text]][lang])
                return jsonify({"ok":True})
            # استلام إثبات الدفع
            if "photo" in msg or "document" in msg or any(k in text.lower() for k in ["tx","txid","hash","proof","إثبات","تحويل"]):
                pending=load_pending()
                pending[str(chat_id)] = pending.get(str(chat_id),{})
                pending[str(chat_id)]["timestamp"]=time.time()
                pending[str(chat_id)]["username"]=username
                pending[str(chat_id)]["name"]=name
                pending[str(chat_id)]["lang"]=USER_LANG.get(chat_id,"ar")
                save_pending(pending)
                summary=MESSAGES["admin_notify"][pending[str(chat_id)]["lang"]].format(
                    name=name,user_id=chat_id,method=pending[str(chat_id)].get("method",""),text=text[:300])
                send_message(ADMIN_ID,summary,reply_markup=build_admin_keyboard(chat_id))
                send_message(chat_id,MESSAGES["proof_received"][USER_LANG.get(chat_id,"ar")])
                return jsonify({"ok":True})

        # callback_query للأزرار
        if "callback_query" in data:
            cq=data["callback_query"]
            cid=cq["from"]["id"]
            data_str=cq.get("data","")
            api_post("answerCallbackQuery",{"callback_query_id":cq.get("id")})
            if data_str.startswith("admin:") and str(cid)==str(ADMIN_ID):
                _,action,user_id=data_str.split(":")
                pending=load_pending()
                info=pending.get(user_id,{})
                lang=info.get("lang","ar")
                if action=="confirm":
                    send_message(user_id,MESSAGES["confirm"][lang].format(VIP_LINK=VIP_LINK))
                    log_payment([time.time(),user_id,info.get("username",""),info.get("name",""),info.get("method",""),cid])
                    send_message(ADMIN_ID,f"✅ تم تأكيد المستخدم {user_id} وتم إرسال رابط القناة.")
                    pending.pop(user_id,None)
                    save_pending(pending)
                elif action=="reject":
                    send_message(user_id,MESSAGES["reject"][lang])
                    send_message(ADMIN_ID,f"🚫 تم رفض المستخدم {user_id}.")
                    pending.pop(user_id,None)
                    save_pending(pending)
                return jsonify({"ok":True})

        return jsonify({"ok":True})
    except Exception as e:
        os.makedirs("logs",exist_ok=True)
        with open("logs/errors.log","a",encoding="utf-8") as f:
            f.write(str(e)+"\n")
        return jsonify({"ok":False,"error":str(e)}),500

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)))
