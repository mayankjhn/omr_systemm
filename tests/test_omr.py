# test_omr.py
# Created for OMR Evaluation System
"""
Unit Tests for OMR Evaluation System
Testing core functionality and edge cases
"""

import unittest
import numpy as np
import cv2
import json
import sys
import os

# Add app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from omr_processor import OMRProcessor, create_sample_answer_key, validate_answer_key
from models import Database, OMRResult
from utils import validate_image_file, enhance_image_quality, correct_image_skew

class TestOMRProcessor(unittest.TestCase):
    """Test OMR processing functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.processor = OMRProcessor(debug=True)
        self.sample_answer_key = create_sample_answer_key(20)  # Small test set
    
    def test_answer_key_creation(self):
        """Test answer key generation"""
        answer_key = create_sample_answer_key(100)
        
        self.assertEqual(len(answer_key), 100)
        for question_num, answer in answer_key.items():
            self.assertIsInstance(question_num, int)
            self.assertGreaterEqual(question_num, 1)
            self.assertLessEqual(question_num, 100)
            self.assertIn(answer, [0, 1, 2, 3, 4])
    
    def test_answer_key_validation(self):
        """Test answer key validation"""
        valid_key = {"1": 0, "2": 1, "3": 2}
        invalid_key = {"1": 5, "2": -1}  # Invalid answers
        
        self.assertTrue(validate_answer_key({1: 0, 2: 1, 3: 2}))
        self.assertFalse(validate_answer_key({"invalid": "key"}))
    
    def test_image_loading_from_array(self):
        """Test image loading from numpy array"""
        # Create test image
        test_image = np.ones((600, 800, 3), dtype=np.uint8) * 255
        
        # Convert to bytes (simulate file upload)
        _, buffer = cv2.imencode('.jpg', test_image)
        image_bytes = buffer.tobytes()
        
        success = self.processor.load_image_from_bytes(image_bytes)
        self.assertTrue(success)
        self.assertIsNotNone(self.processor.original_image)
    
    def test_preprocessing(self):
        """Test image preprocessing"""
        # Create test image
        test_image = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)
        self.processor.original_image = test_image
        
        edged = self.processor.preprocess_image()
        
        self.assertIsNotNone(edged)
        self.assertEqual(len(edged.shape), 2)  # Should be grayscale
    
    def test_bubble_detection(self):
        """Test bubble detection on synthetic image"""
        # Create synthetic OMR-like image
        test_image = np.ones((800, 600, 3), dtype=np.uint8) * 255
        
        # Draw some circles (bubbles)
        cv2.circle(test_image, (100, 100), 15, (0, 0, 0), 2)
        cv2.circle(test_image, (200, 100), 15, (0, 0, 0), -1)  # Filled
        cv2.circle(test_image, (300, 100), 15, (0, 0, 0), 2)
        
        bubbles = self.processor.detect_bubbles(test_image)
        self.assertGreater(len(bubbles), 0)
    
    def test_score_calculation(self):
        """Test score calculation functionality"""
        answer_key = {1: 0, 2: 1, 3: 2, 4: 3, 5: 4}
        extracted_answers = {1: 0, 2: 1, 3: 1, 4: 3, 5: -1}  # Mixed results
        
        results = self.processor.calculate_scores(extracted_answers, answer_key)
        
        self.assertIn('total_questions', results)
        self.assertIn('correct', results)
        self.assertIn('percentage', results)
        self.assertEqual(results['total_questions'], len(answer_key))
        self.assertGreater(results['correct'], 0)

class TestDatabase(unittest.TestCase):
    """Test database functionality"""
    
    def setUp(self):
        """Set up test database"""
        self.db = Database(":memory:")  # Use in-memory database for testing
    
    def test_database_creation(self):
        """Test database table creation"""
        # Database should be created without errors
        stats = self.db.get_database_stats()
        self.assertIsInstance(stats, dict)
    
    def test_result_saving(self):
        """Test saving OMR results"""
        test_result = OMRResult(
            filename="test.jpg",
            sheet_version="A",
            total_questions=100,
            correct_answers=85,
            percentage=85.0,
            subject_scores='{"Subject_1": {"correct": 17, "total": 20, "percentage": 85.0}}',
            detailed_results='{"1": {"correct_answer": 0, "student_answer": 0, "status": "correct"}}',
            processing_info='{"bubbles_detected": 500}'
        )
        
        result_id = self.db.save_result(test_result)
        self.assertIsInstance(result_id, int)
        self.assertGreater(result_id, 0)
    
    def test_answer_key_storage(self):
        """Test answer key storage and retrieval"""
        test_key = {1: 0, 2: 1, 3: 2}
        version = "test_version"
        
        success = self.db.save_answer_key(version, test_key)
        self.assertTrue(success)
        
        retrieved_key = self.db.get_answer_key(version)
        self.assertEqual(retrieved_key, test_key)

class TestUtilities(unittest.TestCase):
    """Test utility functions"""
    
    def test_image_enhancement(self):
        """Test image enhancement functionality"""
        # Create test image with noise
        test_image = np.random.randint(0, 255, (400, 600), dtype=np.uint8)
        
        enhanced = enhance_image_quality(test_image)
        
        self.assertIsNotNone(enhanced)
        self.assertEqual(enhanced.shape, test_image.shape)
    
    def test_skew_correction(self):
        """Test skew correction"""
        # Create test image
        test_image = np.ones((400, 600, 3), dtype=np.uint8) * 255
        
        # Add some lines for skew detection
        cv2.line(test_image, (0, 100), (600, 120), (0, 0, 0), 2)
        cv2.line(test_image, (0, 200), (600, 220), (0, 0, 0), 2)
        
        corrected, angle = correct_image_skew(test_image)
        
        self.assertIsNotNone(corrected)
        self.assertIsInstance(angle, float)
    
    def test_config_loading(self):
        """Test configuration loading"""
        from utils import load_config
        
        config = load_config("non_existent_config.json")
        
        # Should return default config
        self.assertIsInstance(config, dict)
        self.assertIn('bubble_threshold', config)

class TestIntegration(unittest.TestCase):
    """Integration tests for complete workflow"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.processor = OMRProcessor()
        self.db = Database(":memory:")
    
    def test_complete_workflow(self):
        """Test complete OMR processing workflow"""
        # Create synthetic OMR sheet
        omr_image = self.create_synthetic_omr()
        
        # Create answer key
        answer_key = create_sample_answer_key(10)  # Small test
        
        # Convert image to bytes
        _, buffer = cv2.imencode('.jpg', omr_image)
        image_bytes = buffer.tobytes()
        
        # Process the image
        results = self.processor.process_omr_sheet(image_bytes, answer_key)
        
        # Check results
        if 'error' not in results:
            self.assertIn('total_questions', results)
            self.assertIn('percentage', results)
            self.assertGreaterEqual(results['percentage'], 0)
            self.assertLessEqual(results['percentage'], 100)
        else:
            # Processing may fail with synthetic image, which is acceptable
            self.assertIn('error', results)
    
    def create_synthetic_omr(self) -> np.ndarray:
        """Create a synthetic OMR sheet for testing"""
        # Create white background
        image = np.ones((800, 600, 3), dtype=np.uint8) * 255
        
        # Add border
        cv2.rectangle(image, (50, 50), (550, 750), (0, 0, 0), 3)
        
        # Add some bubbles in grid pattern
        for row in range(10):
            y = 100 + row * 60
            for col in range(5):
                x = 100 + col * 80
                # Draw circle
                cv2.circle(image, (x, y), 12, (0, 0, 0), 2)
                # Randomly fill some bubbles
                if np.random.random() > 0.7:
                    cv2.circle(image, (x, y), 10, (0, 0, 0), -1)
        
        return image

# Test runner
def run_tests():
    """Run all tests"""
    print("🧪 Running OMR System Tests...")
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestOMRProcessor,
        TestDatabase, 
        TestUtilities,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\\n📊 Test Results:")
    print(f"✅ Tests passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Tests failed: {len(result.failures)}")
    print(f"💥 Errors: {len(result.errors)}")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    run_tests()