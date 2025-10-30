import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)


class VideoProcessor:
    
    
    def __init__(self, interval=5, max_frames=50):
        
        self.interval = interval
        self.max_frames = max_frames
        logger.info(f"VideoProcessor initialized: interval={interval}s, max_frames={max_frames}")
    
    def extract_frames(self, video_path):
        
        logger.info(f"Processing video: {video_path}")
        
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            logger.error(f"Cannot open video: {video_path}")
            return []
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        
        logger.info(f"Video duration: {int(duration)} seconds")
        logger.info(f"Total frames in video: {total_frames}, FPS: {fps}")
        
        frame_interval = int(fps * self.interval)
        estimated_frames = int(duration / self.interval)
        
        if estimated_frames > self.max_frames:
            frame_interval = int(total_frames / self.max_frames)
            logger.info(f"Adjusted interval to extract max {self.max_frames} frames")
        
        frames = []
        current_frame = 0
        extracted_count = 0
        
        prev_frame = None
        
        while cap.isOpened() and extracted_count < self.max_frames:
            ret, frame = cap.read()
            
            if not ret:
                break
            
            if current_frame % frame_interval == 0:
                timestamp = current_frame / fps
                
                if prev_frame is None or self._is_scene_change(prev_frame, frame):
                    logger.info(f"Extracted frame at {int(timestamp)}s (frame {current_frame})")
                    
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frames.append(frame_rgb)
                    extracted_count += 1
                    
                    prev_frame = frame.copy()
            
            current_frame += 1
        
        cap.release()
        
        logger.info(f"Total frames extracted: {len(frames)}")
        logger.info(f"Coverage: {len(frames) * self.interval}s of {int(duration)}s video")
        
        return frames
    
    def _is_scene_change(self, frame1, frame2, threshold=30.0):
        
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
        
        diff = cv2.absdiff(gray1, gray2)
        mean_diff = np.mean(diff)
        
        return mean_diff > threshold
    
    def get_video_metadata(self, video_path):
        
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            logger.error(f"Cannot open video for metadata: {video_path}")
            return {}
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = total_frames / fps if fps > 0 else 0
        
        cap.release()
        
        metadata = {
            'duration': int(duration),
            'fps': fps,
            'total_frames': total_frames,
            'width': width,
            'height': height,
            'resolution': f"{width}x{height}"
        }
        
        logger.info(f"Video metadata: {metadata}")
        return metadata