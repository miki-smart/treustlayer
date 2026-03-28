"""
Face verification service using face_recognition library.

Features:
- Face detection
- Liveness detection (basic)
- Spoof detection (basic)
- Face matching with ID document

MVP note: liveness/spoof scores are heuristic (face size / simple proxies), not
production-grade presentation-attack detection.
"""
import io
import logging
from typing import Tuple

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class FaceVerificationService:
    """
    Face verification service.
    
    Uses face_recognition library (based on dlib).
    """
    
    async def verify_face(
        self,
        face_image_bytes: bytes,
        id_photo_bytes: bytes | None = None
    ) -> Tuple[float, float, float]:
        """
        Verify face image.
        
        Returns:
            (liveness_score, spoof_probability, quality_score)
        """
        try:
            import face_recognition

            face_image = face_recognition.load_image_file(
                Image.open(io.BytesIO(face_image_bytes))
            )

            face_locations = face_recognition.face_locations(face_image)
            
            if not face_locations:
                logger.warning("No face detected in image")
                return 0.0, 1.0, 0.0
            
            if len(face_locations) > 1:
                logger.warning("Multiple faces detected")
                return 0.5, 0.8, 0.5
            
            liveness_score = self._estimate_liveness(face_image, face_locations[0])
            spoof_probability = 1.0 - liveness_score
            quality_score = self._estimate_quality(face_image, face_locations[0])
            
            return liveness_score, spoof_probability, quality_score
            
        except Exception as e:
            logger.error(f"Face verification error: {e}")
            return 0.0, 1.0, 0.0
    
    async def match_faces(
        self,
        face_image_bytes: bytes,
        id_photo_bytes: bytes
    ) -> float:
        """
        Match face image with ID document photo.
        
        Returns:
            similarity_score (0-1)
        """
        try:
            import face_recognition

            face_image = face_recognition.load_image_file(
                Image.open(io.BytesIO(face_image_bytes))
            )
            id_image = face_recognition.load_image_file(
                Image.open(io.BytesIO(id_photo_bytes))
            )
            
            face_encodings = face_recognition.face_encodings(face_image)
            id_encodings = face_recognition.face_encodings(id_image)
            
            if not face_encodings or not id_encodings:
                logger.warning("Could not extract face encodings")
                return 0.0
            
            face_distance = face_recognition.face_distance([id_encodings[0]], face_encodings[0])[0]
            
            similarity = 1.0 - face_distance
            
            return max(0.0, min(1.0, similarity))
            
        except Exception as e:
            logger.error(f"Face matching error: {e}")
            return 0.0
    
    def _estimate_liveness(self, image: np.ndarray, face_location: tuple) -> float:
        """
        Estimate liveness score (basic implementation).
        
        Production: Use dedicated liveness detection model.
        """
        top, right, bottom, left = face_location
        face_height = bottom - top
        face_width = right - left
        
        if face_height < 100 or face_width < 100:
            return 0.3
        
        return 0.75
    
    def _estimate_quality(self, image: np.ndarray, face_location: tuple) -> float:
        """
        Estimate image quality score (basic implementation).
        """
        top, right, bottom, left = face_location
        face_height = bottom - top
        face_width = right - left
        
        if face_height < 150 or face_width < 150:
            return 0.5
        
        return 0.85


face_verification_service = FaceVerificationService()
