from PIL import Image
import torch
from transformers import BlipProcessor, BlipForConditionalGeneration
import numpy as np
from typing import List
import logging

logger = logging.getLogger(__name__)


class VisionCaptioner:
    
    
    def __init__(self):
        logger.info("Loading BLIP model...")
        self.processor = BlipProcessor.from_pretrained(
            "Salesforce/blip-image-captioning-base"
        )
        self.model = BlipForConditionalGeneration.from_pretrained(
            "Salesforce/blip-image-captioning-base"
        )
        
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)
        logger.info(f"BLIP model loaded on {self.device}")
    
    def caption_frame(self, frame: np.ndarray) -> str:
        
        try:
            
            image = Image.fromarray(frame.astype('uint8'), 'RGB')
            
            inputs = self.processor(images=image, return_tensors="pt").to(self.device)
            out = self.model.generate(**inputs, max_length=50)
            caption = self.processor.decode(out[0], skip_special_tokens=True)
            
            logger.info(f"Generated caption: {caption}")
            return caption
            
        except Exception as e:
            logger.error(f"Error generating caption: {str(e)}")
            return "Unable to generate caption"
    
    def caption_frames(self, frames: List[np.ndarray]) -> List[dict]:
        
        captions = []
        for idx, frame in enumerate(frames):
            caption = self.caption_frame(frame)
            captions.append({
                'frame_index': idx,
                'timestamp': f"{idx * 5}s",  
                'caption': caption
            })
        return captions