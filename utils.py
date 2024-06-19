import cv2
from fer import FER
import speech_recognition as sr
from transformers import pipeline
import numpy as np
from pydub import AudioSegment
import logging

# Initialize sentiment analysis model
sentiment_analyzer = pipeline('sentiment-analysis')
recognizer = sr.Recognizer()

def analyze_image(image_path):
    try:
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError("Image not loaded properly.")

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        emotions = []
        for (x, y, w, h) in faces:
            face = image[y:y+h, x:x+w]  # Use the original color image for emotion detection
            emotion = detect_emotion(face)
            emotions.append(emotion)
        return emotions
    except Exception as e:
        logging.error(f"Error analyzing image: {e}")
        return ["error"]

def detect_emotion(face):
    # Initialize the emotion detector
    detector = FER(mtcnn=True)
    
    # Detect emotions
    emotions = detector.detect_emotions(face)
    
    if emotions:
        # Get the dominant emotion
        dominant_emotion = max(emotions[0]['emotions'], key=emotions[0]['emotions'].get)
        return dominant_emotion
    else:
        return "neutral"

def analyze_audio(audio_path):
    try:
        # Convert audio file to wav format
        audio = AudioSegment.from_file(audio_path)
        wav_path = audio_path.replace('.oga', '.wav')
        audio.export(wav_path, format='wav')

        with sr.AudioFile(wav_path) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio)
        sentiment = sentiment_analyzer(text)
        return text, sentiment
    except Exception as e:
        logging.error(f"Error analyzing audio: {e}")
        return "error", [{"label": "neutral"}]
    

def analyze_video(video_path):
    try:
        cap = cv2.VideoCapture(video_path)
        emotions = []

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)

            for (x, y, w, h) in faces:
                face = frame[y:y+h, x:x+w]
                emotion = detect_emotion(face)
                emotions.append(emotion)
        
        cap.release()
        if not emotions:
            return ["neutral"]
        return emotions
    except Exception as e:
        logging.error(f"Error analyzing video: {e}")
        return ["error"]
