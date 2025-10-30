import os
os.environ['TRANSFORMERS_CACHE'] = './model_cache'

from transformers import BlipProcessor, BlipForConditionalGeneration
import torch

print("📥 Téléchargement du modèle BLIP...")
model_name = "Salesforce/blip-image-captioning-base"

processor = BlipProcessor.from_pretrained(model_name)
model = BlipForConditionalGeneration.from_pretrained(model_name)

print("✅ Modèle téléchargé avec succès!")
print(f"📁 Cache location: {os.environ.get('TRANSFORMERS_CACHE')}")