# models.py
# Created for OMR Evaluation System
"""
Database Models for OMR Evaluation System
Handles data storage and retrieval using SQLite
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class OMRResult:
    """Data class for OMR processing results"""
    filename: str
    sheet_version: str
    total_questions: int
    correct_answers: int
    percentage: float
    subject_scores: str  # JSON string
    detailed_results: str  # JSON string
    processing_info: str  # JSON string
    processed_at: str = None
    id: int = None
    
    def __post_init__(self):
        if self.processed_at is None:
            self.processed_at = datetime.now().isoformat()

class Database:
    """Database manager for OMR results"""
    
    def __init__(self, db_path: str = "omr_results.db"):
        """Initialize database connection"""
        self.db_path = db_path
        self.create_tables()
    
    def create_tables(self):
        """Create necessary database tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create results table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS omr_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        filename TEXT NOT NULL,
                        sheet_version TEXT NOT NULL,
                        total_questions INTEGER NOT NULL,
                        correct_answers INTEGER NOT NULL,
                        percentage REAL NOT NULL,
                        subject_scores TEXT NOT NULL,
                        detailed_results TEXT NOT NULL,
                        processing_info TEXT NOT NULL,
                        processed_at TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create answer_keys table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS answer_keys (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        version TEXT NOT NULL,
                        answer_key TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(version)
                    )
                """)
                
                # Create settings table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS settings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        key TEXT UNIQUE NOT NULL,
                        value TEXT NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.commit()
                logger.info("Database tables created successfully")
                
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            raise
    
    def save_result(self, result: OMRResult) -> int:
        """Save OMR processing result to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO omr_results (
                        filename, sheet_version, total_questions, correct_answers,
                        percentage, subject_scores, detailed_results, processing_info, processed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    result.filename,
                    result.sheet_version,
                    result.total_questions,
                    result.correct_answers,
                    result.percentage,
                    result.subject_scores,
                    result.detailed_results,
                    result.processing_info,
                    result.processed_at
                ))
                
                result_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Result saved with ID: {result_id}")
                return result_id
                
        except Exception as e:
            logger.error(f"Error saving result: {e}")
            raise
    
    def get_result(self, result_id: int) -> Optional[OMRResult]:
        """Retrieve a specific result by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM omr_results WHERE id = ?", (result_id,))
                row = cursor.fetchone()
                
                if row:
                    return OMRResult(
                        id=row[0],
                        filename=row[1],
                        sheet_version=row[2],
                        total_questions=row[3],
                        correct_answers=row[4],
                        percentage=row[5],
                        subject_scores=row[6],
                        detailed_results=row[7],
                        processing_info=row[8],
                        processed_at=row[9]
                    )
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving result: {e}")
            return None
    
    def get_all_results(self) -> List[OMRResult]:
        """Retrieve all results from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM omr_results 
                    ORDER BY created_at DESC
                """)
                rows = cursor.fetchall()
                
                results = []
                for row in rows:
                    results.append(OMRResult(
                        id=row[0],
                        filename=row[1],
                        sheet_version=row[2],
                        total_questions=row[3],
                        correct_answers=row[4],
                        percentage=row[5],
                        subject_scores=row[6],
                        detailed_results=row[7],
                        processing_info=row[8],
                        processed_at=row[9]
                    ))
                
                return results
                
        except Exception as e:
            logger.error(f"Error retrieving all results: {e}")
            return []
    
    def save_answer_key(self, version: str, answer_key: Dict) -> bool:
        """Save answer key to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO answer_keys (version, answer_key)
                    VALUES (?, ?)
                """, (version, json.dumps(answer_key)))
                
                conn.commit()
                logger.info(f"Answer key saved for version: {version}")
                return True
                
        except Exception as e:
            logger.error(f"Error saving answer key: {e}")
            return False
    
    def get_answer_key(self, version: str) -> Optional[Dict]:
        """Retrieve answer key for specific version"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    "SELECT answer_key FROM answer_keys WHERE version = ?", 
                    (version,)
                )
                row = cursor.fetchone()
                
                if row:
                    return json.loads(row[0])
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving answer key: {e}")
            return None
    
    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Count total results
                cursor.execute("SELECT COUNT(*) FROM omr_results")
                total_results = cursor.fetchone()[0]
                
                # Count answer keys
                cursor.execute("SELECT COUNT(*) FROM answer_keys")
                total_keys = cursor.fetchone()[0]
                
                # Get average score
                cursor.execute("SELECT AVG(percentage) FROM omr_results")
                avg_score = cursor.fetchone()[0] or 0
                
                # Get date range
                cursor.execute("""
                    SELECT MIN(created_at), MAX(created_at) 
                    FROM omr_results
                """)
                date_range = cursor.fetchone()
                
                return {
                    'total_results': total_results,
                    'total_answer_keys': total_keys,
                    'average_score': round(avg_score, 2),
                    'earliest_result': date_range[0],
                    'latest_result': date_range[1]
                }
                
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}
    
    def clear_all_results(self) -> bool:
        """Clear all results from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM omr_results")
                conn.commit()
                
                logger.info("All results cleared from database")
                return True
                
        except Exception as e:
            logger.error(f"Error clearing results: {e}")
            return False
    
    def save_setting(self, key: str, value: str) -> bool:
        """Save application setting"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO settings (key, value, updated_at)
                    VALUES (?, ?, ?)
                """, (key, value, datetime.now().isoformat()))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error saving setting: {e}")
            return False
    
    def get_setting(self, key: str, default: str = None) -> Optional[str]:
        """Retrieve application setting"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
                row = cursor.fetchone()
                
                return row[0] if row else default
                
        except Exception as e:
            logger.error(f"Error retrieving setting: {e}")
            return default

class AnalyticsEngine:
    """Analytics engine for OMR results"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def generate_performance_report(self) -> Dict:
        """Generate comprehensive performance report"""
        results = self.db.get_all_results()
        
        if not results:
            return {'error': 'No data available'}
        
        # Basic statistics
        scores = [result.percentage for result in results]
        
        report = {
            'summary': {
                'total_sheets': len(results),
                'average_score': sum(scores) / len(scores),
                'median_score': sorted(scores)[len(scores) // 2],
                'max_score': max(scores),
                'min_score': min(scores),
                'std_deviation': self._calculate_std(scores)
            },
            'distribution': self._analyze_score_distribution(scores),
            'trends': self._analyze_trends(results),
            'subject_analysis': self._analyze_subjects(results)
        }
        
        return report
    
    def _calculate_std(self, scores: List[float]) -> float:
        """Calculate standard deviation"""
        if len(scores) < 2:
            return 0.0
            
        mean = sum(scores) / len(scores)
        variance = sum((score - mean) ** 2 for score in scores) / len(scores)
        return variance ** 0.5
    
    def _analyze_score_distribution(self, scores: List[float]) -> Dict:
        """Analyze score distribution"""
        ranges = {
            '90-100%': 0,
            '80-89%': 0,
            '70-79%': 0,
            '60-69%': 0,
            '50-59%': 0,
            'Below 50%': 0
        }
        
        for score in scores:
            if score >= 90:
                ranges['90-100%'] += 1
            elif score >= 80:
                ranges['80-89%'] += 1
            elif score >= 70:
                ranges['70-79%'] += 1
            elif score >= 60:
                ranges['60-69%'] += 1
            elif score >= 50:
                ranges['50-59%'] += 1
            else:
                ranges['Below 50%'] += 1
        
        return ranges
    
    def _analyze_trends(self, results: List[OMRResult]) -> Dict:
        """Analyze performance trends over time"""
        # Sort by processing date
        sorted_results = sorted(results, key=lambda x: x.processed_at)
        
        if len(sorted_results) < 2:
            return {'trend': 'insufficient_data'}
        
        # Calculate trend (simple linear trend)
        scores = [r.percentage for r in sorted_results]
        n = len(scores)
        
        # Linear regression slope calculation
        x_vals = list(range(n))
        x_mean = sum(x_vals) / n
        y_mean = sum(scores) / n
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_vals, scores))
        denominator = sum((x - x_mean) ** 2 for x in x_vals)
        
        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator
        
        trend_direction = 'improving' if slope > 0.1 else 'declining' if slope < -0.1 else 'stable'
        
        return {
            'trend': trend_direction,
            'slope': slope,
            'first_score': scores[0],
            'last_score': scores[-1],
            'improvement': scores[-1] - scores[0]
        }
    
    def _analyze_subjects(self, results: List[OMRResult]) -> Dict:
        """Analyze subject-wise performance"""
        subject_data = {}
        
        for result in results:
            try:
                subjects = json.loads(result.subject_scores)
                for subject, scores in subjects.items():
                    if subject not in subject_data:
                        subject_data[subject] = []
                    subject_data[subject].append(scores['percentage'])
            except (json.JSONDecodeError, KeyError):
                continue
        
        subject_analysis = {}
        for subject, scores in subject_data.items():
            if scores:
                subject_analysis[subject] = {
                    'average': sum(scores) / len(scores),
                    'max': max(scores),
                    'min': min(scores),
                    'count': len(scores)
                }
        
        return subject_analysis

# Utility functions for data export
def export_results_to_csv(results: List[OMRResult]) -> str:
    """Export results to CSV format"""
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'ID', 'Filename', 'Sheet Version', 'Total Questions', 
        'Correct Answers', 'Percentage', 'Processed At'
    ])
    
    # Write data
    for result in results:
        writer.writerow([
            result.id, result.filename, result.sheet_version,
            result.total_questions, result.correct_answers,
            f"{result.percentage:.2f}%", result.processed_at
        ])
    
    return output.getvalue()

def export_detailed_results(results: List[OMRResult]) -> str:
    """Export detailed results including subject scores"""
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'ID', 'Filename', 'Sheet Version', 'Total Questions', 'Correct',
        'Incorrect', 'Not Attempted', 'Multiple Marked', 'Percentage',
        'Subject_1_Score', 'Subject_2_Score', 'Subject_3_Score',
        'Subject_4_Score', 'Subject_5_Score', 'Processed At'
    ])
    
    # Write data
    for result in results:
        try:
            subjects = json.loads(result.subject_scores)
            detailed = json.loads(result.detailed_results)
            
            subject_scores = []
            for i in range(1, 6):
                subject_key = f'Subject_{i}'
                if subject_key in subjects:
                    subject_scores.append(f"{subjects[subject_key]['percentage']:.1f}%")
                else:
                    subject_scores.append('N/A')
            
            # Calculate stats from detailed results
            incorrect = sum(1 for q in detailed.values() if q['status'] == 'incorrect')
            not_attempted = sum(1 for q in detailed.values() if q['status'] == 'not_attempted')
            multiple_marked = sum(1 for q in detailed.values() if q['status'] == 'multiple_marked')
            
            writer.writerow([
                result.id, result.filename, result.sheet_version,
                result.total_questions, result.correct_answers,
                incorrect, not_attempted, multiple_marked,
                f"{result.percentage:.2f}%"
            ] + subject_scores + [result.processed_at])
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error processing result {result.id}: {e}")
            continue
    
    return output.getvalue()# End of models.py