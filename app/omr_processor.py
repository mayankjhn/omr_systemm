# HYPER-TUNED omr_processor.py
import cv2
import numpy as np
import imutils

class OMRProcessor:
    def __init__(self, debug=False):
        self.debug = debug
        self.processed_image_for_debug = None

    def process_omr_sheet(self, image_bytes, answer_key: dict):
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if image is None: return {'error': 'Failed to decode image.'}

            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Use adaptive thresholding, a powerful technique for uneven lighting
            thresh = cv2.adaptiveThreshold(gray, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 21, 10)

            # Find contours on the thresholded image
            contours = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            contours = imutils.grab_contours(contours)
            
            question_cnts = []
            for c in contours:
                (x, y, w, h) = cv2.boundingRect(c)
                ar = w / float(h)
                # EXTREMELY lenient parameters to find anything that looks like a bubble
                if w >= 10 and h >= 10 and 0.5 <= ar <= 1.5:
                    # Further check if the contour is somewhat circular
                    if cv2.contourArea(c) > 50:
                        question_cnts.append(c)

            if len(question_cnts) < 400:
                return {'error': f'Bubble detection failed (found {len(question_cnts)}). The sample images are not compatible with this CV approach.'}

            # Sort contours from top-to-bottom
            question_cnts = imutils.contours.sort_contours(question_cnts, method="top-to-bottom")[0]
            
            correct = 0
            total_questions = 100
            options_per_question = 4

            # Group bubbles into rows of 20 (5 questions * 4 options)
            for (q_row, i) in enumerate(np.arange(0, len(question_cnts), 20)):
                if q_row >= 20: break # Process only 20 rows of questions

                # Sort the bubbles in the current row from left-to-right
                row_contours = imutils.contours.sort_contours(question_cnts[i:i + 20])[0]
                
                # Iterate through the 5 question blocks in the row
                for col in range(5):
                    question_num = (col * 20) + q_row + 1
                    
                    # Get the 4 bubbles for this question
                    cnts = row_contours[col * options_per_question : (col + 1) * options_per_question]
                    bubbled = None
                    
                    for (j, c) in enumerate(cnts):
                        mask = np.zeros(thresh.shape, dtype="uint8")
                        cv2.drawContours(mask, [c], -1, 255, -1)
                        mask = cv2.bitwise_and(thresh, thresh, mask=mask)
                        total = cv2.countNonZero(mask)
                        if bubbled is None or total > bubbled[0]:
                            bubbled = (total, j)
                    
                    correct_answer_idx = answer_key.get(str(question_num))
                    if correct_answer_idx is not None and bubbled[1] == correct_answer_idx:
                        correct += 1

            score = (correct / total_questions) * 100
            return {'total_questions': total_questions, 'correct': correct, 'percentage': score, 'error': None}
        except Exception:
            return {'error': 'A critical error occurred during image processing.'}
