# utils.py
# Created for OMR Evaluation System
"""
Utility Functions for OMR Evaluation System
Helper functions for file handling, image processing, and report generation
"""

import os
import cv2
import numpy as np
import base64
import io
import uuid
import tempfile
import zipfile
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
import json
import logging

logger = logging.getLogger(__name__)

# File handling utilities
def save_uploaded_file(uploaded_file, upload_dir: str = "uploads") -> str:
    """Save uploaded file to temporary directory"""
    try:
        # Create upload directory if it doesn't exist
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        file_extension = os.path.splitext(uploaded_file.name)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        logger.info(f"File saved: {file_path}")
        return file_path
        
    except Exception as e:
        logger.error(f"Error saving uploaded file: {e}")
        raise

def create_download_link(data: str, filename: str, mime_type: str = "text/plain") -> str:
    """Create download link for data"""
    b64_data = base64.b64encode(data.encode()).decode()
    href = f'<a href="data:{mime_type};base64,{b64_data}" download="{filename}">Download {filename}</a>'
    return href

def validate_image_file(file) -> bool:
    """Validate uploaded image file"""
    try:
        # Check file size (max 10MB)
        if hasattr(file, 'size') and file.size > 10 * 1024 * 1024:
            logger.warning(f"File too large: {file.size} bytes")
            return False
        
        # Check file extension
        if hasattr(file, 'name'):
            valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']
            file_extension = os.path.splitext(file.name)[1].lower()
            if file_extension not in valid_extensions:
                logger.warning(f"Invalid file extension: {file_extension}")
                return False
        
        # Try to load as image
        if hasattr(file, 'read'):
            file_bytes = file.read()
            file.seek(0)  # Reset file pointer
            
            # Validate image can be loaded
            nparr = np.frombuffer(file_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                logger.warning("Could not decode image")
                return False
                
            # Check image dimensions
            height, width = img.shape[:2]
            if width < 400 or height < 300:
                logger.warning(f"Image too small: {width}x{height}")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating image: {e}")
        return False

# Image processing utilities
def enhance_image_quality(image: np.ndarray) -> np.ndarray:
    """Enhance image quality for better OMR processing"""
    try:
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(enhanced)
        
        return denoised
        
    except Exception as e:
        logger.error(f"Error enhancing image: {e}")
        return image

def correct_image_skew(image: np.ndarray) -> Tuple[np.ndarray, float]:
    """Correct image skew using Hough Transform"""
    try:
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Apply edge detection
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # Apply Hough Line Transform
        lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=100)
        
        if lines is None:
            return image, 0.0
        
        # Calculate angles
        angles = []
        for rho, theta in lines[:, 0]:
            angle = theta * 180 / np.pi
            if angle < 45:
                angles.append(angle)
            elif angle > 135:
                angles.append(angle - 180)
        
        if not angles:
            return image, 0.0
        
        # Calculate median angle
        median_angle = np.median(angles)
        
        # Rotate image to correct skew
        if abs(median_angle) > 0.5:  # Only correct if skew is significant
            (h, w) = image.shape[:2]
            center = (w // 2, h // 2)
            rotation_matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)
            corrected = cv2.warpAffine(image, rotation_matrix, (w, h))
            return corrected, median_angle
        
        return image, 0.0
        
    except Exception as e:
        logger.error(f"Error correcting skew: {e}")
        return image, 0.0

def create_debug_image(original: np.ndarray, contours: List, bubbles: List[Dict]) -> np.ndarray:
    """Create debug image showing detected contours and bubbles"""
    try:
        # Create color version of image
        if len(original.shape) == 2:
            debug_img = cv2.cvtColor(original, cv2.COLOR_GRAY2BGR)
        else:
            debug_img = original.copy()
        
        # Draw all contours in blue
        cv2.drawContours(debug_img, contours, -1, (255, 0, 0), 2)
        
        # Draw detected bubbles
        for bubble in bubbles:
            center = bubble['center']
            is_filled = bubble.get('is_filled', False)
            
            # Color based on fill status
            color = (0, 255, 0) if is_filled else (0, 0, 255)  # Green if filled, red if not
            
            # Draw circle
            cv2.circle(debug_img, center, 10, color, 2)
            
            # Draw fill percentage text
            fill_pct = bubble.get('fill_percentage', 0) * 100
            cv2.putText(debug_img, f"{fill_pct:.1f}%", 
                       (center[0] - 20, center[1] - 15),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.3, color, 1)
        
        return debug_img
        
    except Exception as e:
        logger.error(f"Error creating debug image: {e}")
        return original

# Report generation utilities
def generate_score_summary(results: Dict) -> str:
    """Generate text summary of OMR results"""
    try:
        summary_lines = [
            "=" * 50,
            "OMR EVALUATION SUMMARY",
            "=" * 50,
            f"Total Questions: {results['total_questions']}",
            f"Correct Answers: {results['correct']}",
            f"Incorrect Answers: {results['incorrect']}",
            f"Not Attempted: {results['not_attempted']}",
            f"Multiple Marked: {results['multiple_marked']}",
            f"Overall Score: {results['percentage']:.2f}%",
            "",
            "SUBJECT-WISE PERFORMANCE:",
            "-" * 30
        ]
        
        # Add subject scores
        if 'subject_scores' in results:
            for subject, scores in results['subject_scores'].items():
                summary_lines.append(
                    f"{subject}: {scores['correct']}/{scores['total']} ({scores['percentage']:.1f}%)"
                )
        
        summary_lines.extend([
            "",
            f"Processed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 50
        ])
        
        return "\\n".join(summary_lines)
        
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        return "Error generating summary"

def create_results_json(results: List[Dict]) -> str:
    """Create JSON format of results for export"""
    try:
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'total_sheets': len(results),
            'results': results,
            'summary_statistics': {
                'average_score': np.mean([r['percentage'] for r in results]),
                'max_score': max([r['percentage'] for r in results]),
                'min_score': min([r['percentage'] for r in results]),
                'total_questions_processed': sum([r['total_questions'] for r in results]),
                'total_correct_answers': sum([r['correct'] for r in results])
            }
        }
        
        return json.dumps(export_data, indent=2)
        
    except Exception as e:
        logger.error(f"Error creating JSON export: {e}")
        return "{}"

def generate_report_pdf(results: Dict, filename: str) -> Optional[str]:
    """Generate PDF report (placeholder - would require reportlab)"""
    # This is a placeholder function
    # In a full implementation, you would use libraries like reportlab
    # to generate professional PDF reports
    try:
        report_html = f"""
        <html>
        <head>
            <title>OMR Evaluation Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ text-align: center; color: #333; }}
                .summary {{ background: #f5f5f5; padding: 20px; border-radius: 5px; }}
                .subject-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                .subject-table th, .subject-table td {{ 
                    border: 1px solid #ddd; padding: 8px; text-align: left; 
                }}
                .subject-table th {{ background-color: #4CAF50; color: white; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>OMR Evaluation Report</h1>
                <p>Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
            </div>
            
            <div class="summary">
                <h2>Summary</h2>
                <p><strong>Total Questions:</strong> {results['total_questions']}</p>
                <p><strong>Correct Answers:</strong> {results['correct']}</p>
                <p><strong>Overall Score:</strong> {results['percentage']:.2f}%</p>
            </div>
            
            <h2>Subject-wise Performance</h2>
            <table class="subject-table">
                <tr>
                    <th>Subject</th>
                    <th>Correct</th>
                    <th>Total</th>
                    <th>Percentage</th>
                </tr>
        """
        
        # Add subject rows
        if 'subject_scores' in results:
            for subject, scores in results['subject_scores'].items():
                report_html += f"""
                <tr>
                    <td>{subject}</td>
                    <td>{scores['correct']}</td>
                    <td>{scores['total']}</td>
                    <td>{scores['percentage']:.1f}%</td>
                </tr>
                """
        
        report_html += """
            </table>
        </body>
        </html>
        """
        
        # Save HTML file (in real implementation, convert to PDF)
        html_filename = filename.replace('.pdf', '.html')
        with open(html_filename, 'w') as f:
            f.write(report_html)
        
        return html_filename
        
    except Exception as e:
        logger.error(f"Error generating PDF report: {e}")
        return None

# Batch processing utilities
def process_images_batch(image_paths: List[str], answer_key: Dict, 
                        processor, progress_callback=None) -> List[Dict]:
    """Process multiple images in batch"""
    results = []
    
    for i, image_path in enumerate(image_paths):
        try:
            # Update progress
            if progress_callback:
                progress_callback(i, len(image_paths), image_path)
            
            # Process image
            result = processor.process_omr_sheet(image_path, answer_key)
            
            if 'error' not in result:
                result['filename'] = os.path.basename(image_path)
                result['processed_at'] = datetime.now().isoformat()
                results.append(result)
            else:
                logger.error(f"Error processing {image_path}: {result['error']}")
                
        except Exception as e:
            logger.error(f"Unexpected error processing {image_path}: {e}")
    
    return results

def create_batch_report(results: List[Dict]) -> Dict:
    """Create comprehensive batch processing report"""
    if not results:
        return {'error': 'No results to analyze'}
    
    # Calculate statistics
    scores = [r['percentage'] for r in results]
    correct_answers = [r['correct'] for r in results]
    
    batch_report = {
        'processing_summary': {
            'total_sheets': len(results),
            'successfully_processed': len(results),
            'average_score': np.mean(scores),
            'median_score': np.median(scores),
            'std_deviation': np.std(scores),
            'min_score': min(scores),
            'max_score': max(scores)
        },
        'score_distribution': {
            'excellent (90-100%)': len([s for s in scores if s >= 90]),
            'good (80-89%)': len([s for s in scores if 80 <= s < 90]),
            'average (70-79%)': len([s for s in scores if 70 <= s < 80]),
            'below_average (60-69%)': len([s for s in scores if 60 <= s < 70]),
            'poor (<60%)': len([s for s in scores if s < 60])
        },
        'detailed_results': results,
        'generated_at': datetime.now().isoformat()
    }
    
    return batch_report

# Configuration utilities
def load_config(config_file: str = "config.json") -> Dict:
    """Load configuration from file"""
    default_config = {
        'bubble_threshold': 0.6,
        'min_bubble_area': 100,
        'max_bubble_area': 2000,
        'circularity_threshold': 0.3,
        'questions_per_subject': 20,
        'num_subjects': 5,
        'debug_mode': False
    }
    
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
            # Merge with defaults
            default_config.update(config)
            return default_config
        else:
            # Create default config file
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            return default_config
            
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return default_config

def save_config(config: Dict, config_file: str = "config.json") -> bool:
    """Save configuration to file"""
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving config: {e}")
        return False

# Validation utilities
def validate_answer_key_file(file_content: str) -> Tuple[bool, str, Optional[Dict]]:
    """Validate answer key file content"""
    try:
        # Parse JSON
        answer_key = json.loads(file_content)
        
        if not isinstance(answer_key, dict):
            return False, "Answer key must be a JSON object", None
        
        # Validate structure
        for question_num, answer in answer_key.items():
            # Convert string keys to integers
            try:
                q_num = int(question_num)
            except ValueError:
                return False, f"Question number '{question_num}' is not a valid integer", None
            
            if q_num < 1 or q_num > 200:  # Reasonable range
                return False, f"Question number {q_num} is out of range (1-200)", None
            
            if not isinstance(answer, int) or answer < 0 or answer > 4:
                return False, f"Answer for question {q_num} must be an integer 0-4 (A-E)", None
        
        # Convert all keys to integers
        validated_key = {int(k): v for k, v in answer_key.items()}
        
        return True, f"Valid answer key with {len(validated_key)} questions", validated_key
        
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON format: {str(e)}", None
    except Exception as e:
        return False, f"Validation error: {str(e)}", None

def create_sample_omr_image(width: int = 800, height: int = 1200) -> np.ndarray:
    """Create a sample OMR sheet image for testing"""
    try:
        # Create white background
        image = np.ones((height, width, 3), dtype=np.uint8) * 255
        
        # Convert to PIL for easier drawing
        pil_image = Image.fromarray(image)
        draw = ImageDraw.Draw(pil_image)
        
        # Draw title
        draw.text((width//2 - 100, 50), "SAMPLE OMR SHEET", fill=(0, 0, 0))
        
        # Draw bubbles for 100 questions (20 rows x 5 columns)
        bubble_radius = 8
        start_x = 100
        start_y = 150
        col_spacing = 30
        row_spacing = 40
        
        question_num = 1
        
        for row in range(20):  # 20 rows
            y = start_y + row * row_spacing
            
            # Question number
            draw.text((50, y - 5), str(question_num), fill=(0, 0, 0))
            
            for col in range(5):  # 5 options (A, B, C, D, E)
                x = start_x + col * col_spacing
                
                # Draw bubble circle
                draw.ellipse([x - bubble_radius, y - bubble_radius, 
                            x + bubble_radius, y + bubble_radius], 
                           outline=(0, 0, 0), width=2)
                
                # Draw option letter
                option_letter = chr(ord('A') + col)
                draw.text((x - 3, y - 25), option_letter, fill=(0, 0, 0))
            
            question_num += 1
            
            # Add more columns for remaining questions
            if question_num <= 100 and question_num % 20 == 1:
                start_x += 200  # Move to next column group
                if start_x > width - 200:
                    start_x = 100
                    start_y += 500  # Move to next row group
        
        # Convert back to numpy array
        return np.array(pil_image)
        
    except Exception as e:
        logger.error(f"Error creating sample OMR image: {e}")
        # Return blank white image as fallback
        return np.ones((height, width, 3), dtype=np.uint8) * 255

# Logging utilities
def setup_logging(log_level: str = "INFO", log_file: str = "omr_system.log"):
    """Setup logging configuration"""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logger.info("Logging configured successfully")

# Error handling utilities
def handle_processing_error(error: Exception, context: str) -> Dict:
    """Standard error handling for processing operations"""
    error_msg = f"Error in {context}: {str(error)}"
    logger.error(error_msg)
    
    return {
        'error': True,
        'message': error_msg,
        'context': context,
        'timestamp': datetime.now().isoformat()
    }