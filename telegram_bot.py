from flask import Flask, request, jsonify
import threading
import stripe
import os
import logging
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv
from pymongo import MongoClient
import asyncio
from io import BytesIO
from groq_response import get_groq_response
from utils import analyze_image, analyze_audio, analyze_video

# Load environment variables
load_dotenv()
TELEGRAM_BOT_API_TOKEN = os.getenv('TELEGRAM_BOT_API_TOKEN')
STRIPE_API_KEY = os.getenv('STRIPE_API_KEY')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')
MONGO_URI = os.getenv('MONGO_URI')
NGROK_URL = os.getenv('NGROK_URL')

# Configure Stripe
stripe.api_key = STRIPE_API_KEY

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Setup Flask app
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running"

@app.route('/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    
    logger.info(f"Received Stripe webhook: {payload}")
    logger.info(f"Stripe signature: {sig_header}")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except ValueError as e:
        logger.error(f"Invalid payload: {e}")
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {e}")
        return jsonify({'error': 'Invalid signature'}), 400

    logger.info(f"Stripe event type: {event['type']}")

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_checkout_session(session)
    elif event['type'] == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        handle_invoice_payment_succeeded(invoice)
    elif event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        handle_subscription_updated(subscription)
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        handle_subscription_deleted(subscription)
    else:
        logger.warning(f"Unhandled event type: {event['type']}")

    return '', 200

def handle_checkout_session(session):
    logger.info(f"Checkout session completed: {session}")
    user_id = session.get('client_reference_id')
    users_collection.update_one(
        {"user_id": int(user_id)},
        {"$set": {"subscribed": True}}
    )

def handle_invoice_payment_succeeded(invoice):
    logger.info(f"Invoice payment succeeded: {invoice}")

def handle_subscription_updated(subscription):
    logger.info(f"Subscription updated: {subscription}")
    user_id = subscription.get('metadata', {}).get('user_id')
    if user_id:
        users_collection.update_one(
            {"user_id": int(user_id)},
            {"$set": {"subscribed": subscription['status'] == 'active'}}
        )

def handle_subscription_deleted(subscription):
    logger.info(f"Subscription deleted: {subscription}")
    user_id = subscription.get('metadata', {}).get('user_id')
    if user_id:
        users_collection.update_one(
            {"user_id": int(user_id)},
            {"$set": {"subscribed": False}}
        )

# Function to run Flask app
def run_flask_app():
    app.run(host='0.0.0.0', port=8080)

# MongoDB setup
client = MongoClient(MONGO_URI)
db = client['telegram_bot']
users_collection = db['users']

# Telegram bot setup
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if not users_collection.find_one({"user_id": user_id}):
        users_collection.insert_one({"user_id": user_id, "message_count": 0, "subscribed": False, "conversation_history": []})
    welcome_message = (
        "🤖 The first AI life coach available 24/7 used by thousands of people\n\n"
        "📜 Disclaimer\n"
        "By continuing, you agree to understand I am an AI life coach. I am not a licensed psychologist, "
        "therapist, or healthcare professional and do not replace the care of those. I cannot take any "
        "responsibility for the results of your actions, and any harm you suffer as a result of the use, or "
        "non-use of the information available. Use judgment and due diligence before taking any action or plan "
        "suggested. Do not use if you feel in danger to yourself or others, instead find a professional at findahelpline.com\n\n"
        "✅ Reframe your negative thoughts\n"
        "✅ Take action and get unstuck\n"
        "✅ Get you fit which helps your mind\n"
        "✅ Talk you through your day\n"
        "✅ Feel better by checking up on you\n\n"
        "You can\n"
        "Write /reset at any moment to delete your entire convo history from our servers\n\n"
    )
    await update.message.reply_text(welcome_message)

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    users_collection.update_one({"user_id": user_id}, {"$set": {"conversation_history": []}})
    await update.message.reply_text("Your conversation history has been reset.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE, response_text: str = None) -> None:
    user_id = update.message.from_user.id
    user_data = users_collection.find_one({"user_id": user_id})

    if not user_data:
        users_collection.insert_one({"user_id": user_id, "message_count": 0, "subscribed": False, "conversation_history": []})
        user_data = users_collection.find_one({"user_id": user_id})

    if is_subscription_active(user_data) or user_data['message_count'] < 10:
        conversation_history = user_data.get('conversation_history', [])
        conversation_history_text = "\n".join(
            [f"User: {msg['user']}\nBot: {msg['bot']}" for msg in conversation_history]
        )
        
        if response_text:
            logger.info(f"Received message from user {user_id}: {response_text}")
            full_message = f"{conversation_history_text}\nUser: {response_text}"
            try:
                response = await get_groq_response(full_message)
                await update.message.reply_text(response)
                users_collection.update_one(
                    {"user_id": user_id}, 
                    {"$inc": {"message_count": 1}, "$push": {"conversation_history": {"user": response_text, "bot": response}}}
                )
            except Exception as e:
                logger.error(f"Error generating response: {e}")
                await update.message.reply_text("Sorry, I couldn't process your request.")
        else:
            user_message = update.message.text
            logger.info(f"Received message from user {user_id}: {user_message}")
            full_message = f"{conversation_history_text}\nUser: {user_message}"
            try:
                response = await get_groq_response(full_message)
                await update.message.reply_text(response)
                users_collection.update_one(
                    {"user_id": user_id}, 
                    {"$inc": {"message_count": 1}, "$push": {"conversation_history": {"user": user_message, "bot": response}}}
                )
            except Exception as e:
                logger.error(f"Error generating response: {e}")
                await update.message.reply_text("Sorry, I couldn't process your request.")
    else:
        subscription_url = await create_checkout_session(user_id)
        await update.message.reply_text(f"To continue using the service, please subscribe: {subscription_url}")


async def create_checkout_session(user_id):
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': 'AI Life Coach Subscription',
                },
                'unit_amount': 1000,
                'recurring': {
                    'interval': 'month',
                },
            },
            'quantity': 1,
        }],
        mode='subscription',
        success_url=f"{NGROK_URL}/success.html",
        cancel_url=f"{NGROK_URL}/cancel.html",
        client_reference_id=str(user_id),
    )
    return session.url

def is_subscription_active(user_data):
    return user_data and user_data.get('subscribed', False)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    try:
        file = await update.message.photo[-1].get_file()
        photo_bytes = BytesIO(await file.download_as_bytearray())
        image_path = 'downloads/photo.jpg'

        os.makedirs(os.path.dirname(image_path), exist_ok=True)

        with open(image_path, 'wb') as f:
            f.write(photo_bytes.getbuffer())
        emotions = analyze_image(image_path)
        response_text = f"Detected emotions in the image: {', '.join(emotions)}.\nGenerate a response based on these emotions."
        await handle_message(update, context, response_text=response_text)
    except Exception as e:
        logger.error(f"Error handling photo: {e}")
        await update.message.reply_text("Sorry, I couldn't process the image.")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    try:
        file = await update.message.voice.get_file()
        audio_bytes = BytesIO(await file.download_as_bytearray())
        audio_path = 'downloads/audio.oga'

        os.makedirs(os.path.dirname(audio_path), exist_ok=True)

        with open(audio_path, 'wb') as f:
            f.write(audio_bytes.getbuffer())

        text, sentiment = analyze_audio(audio_path)
        response_text = f"User's sentiment: {sentiment[0]['label']}.\nUser's message: {text}\nResponse:"
        await handle_message(update, context, response_text=response_text)
    except Exception as e:
        logger.error(f"Error handling voice message: {e}")
        await update.message.reply_text("Sorry, I couldn't process the audio message.")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    try:
        file = await update.message.video.get_file()
        video_bytes = BytesIO(await file.download_as_bytearray())
        video_path = 'downloads/video.mp4'

        os.makedirs(os.path.dirname(video_path), exist_ok=True)

        with open(video_path, 'wb') as f:
            f.write(video_bytes.getbuffer())

        emotions = analyze_video(video_path)
        response_text = f"Detected emotions in the video: {', '.join(emotions)}.\nGenerate a response based on these emotions."
        await handle_message(update, context, response_text=response_text)
    except Exception as e:
        logger.error(f"Error handling video: {e}")
        await update.message.reply_text("Sorry, I couldn't process the video message.")

def start_telegram_bot():
    asyncio.set_event_loop(asyncio.new_event_loop())  # Create and set a new event loop for the thread
    application = Application.builder().token(TELEGRAM_BOT_API_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("reset", reset))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))

    logger.info("Starting bot polling")
    application.run_polling()

if __name__ == "__main__":
    # Start the Flask app in a separate thread
    threading.Thread(target=run_flask_app).start()
    
    # Start the Telegram bot in the main thread
    start_telegram_bot()
