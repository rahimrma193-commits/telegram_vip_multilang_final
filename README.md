
Telegram VIP Bot - Multi-language Final Package (main.py) Ready for Render

Features:
- Arabic / English / French messages
- PayPal / USDT / BaridiMob payment handling
- Admin notification with Confirm/Reject buttons
- Auto-add to VIP channel after confirmation
- Log payments in CSV
- Reminders for pending users
- Flask webhook for Render deployment

Deployment:
1. Set environment variables BOT_TOKEN, ADMIN_ID, VIP_INVITE_LINK
2. Deploy on Render
3. Set webhook: https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook?url=https://your-service.onrender.com/webhook
