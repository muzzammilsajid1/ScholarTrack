"""
Service for grade calculations and analytics.
"""
from models.exceptions import InvalidGradeError
from database.db_manager import DatabaseManager

class GradeService:
    """Provides business logic for grades, GPA calculations, and class statistics.
    
    This class demonstrates encapsulation by isolating business logic from direct database operations.
    """
    def __init__(self, db: DatabaseManager):
        """Initializes the service with a database connection.
        
        Args:
            db (DatabaseManager): The active database connection manager.
        """
        self.db = db

    @staticmethod
    def letter_grade(score: float) -> str:
        """Converts a numerical score into a standard letter grade.
        
        Args:
            score (float): The numerical score out of 100.
            
        Returns:
            str: The corresponding letter grade from A to F.
            
        Raises:
            InvalidGradeError: If the score falls outside the 0 to 100 range.
        """
        if not (0 <= score <= 100):
            raise InvalidGradeError(f"Score {score} is out of range. Must be between 0 and 100 inclusive.")
            
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'

    @staticmethod
    def calculate_gpa(scores: list) -> float:
        """Calculates a cumulative Grade Point Average from numerical scores.
        
        Args:
            scores (list): A list of numerical scores.
            
        Returns:
            float: The computed cumulative GPA rounded to two decimals.
        """
        if not scores:
            return 0.0
            
        gpa_scale_map = {'A': 4.0, 'B': 3.0, 'C': 2.0, 'D': 1.0, 'F': 0.0}
        
        total_points = 0.0
        for score in scores:
            letter = GradeService.letter_grade(score)
            total_points += gpa_scale_map[letter]
            
        return round(total_points / len(scores), 2)

    @staticmethod
    def is_at_risk(gpa: float, threshold: float = 2.0) -> bool:
        """Identifies if a student is at risk based on their cumulative GPA.
        
        Args:
            gpa (float): The user's current GPA.
            threshold (float, optional): The warning threshold. Defaults to 2.0.
            
        Returns:
            bool: True if the GPA is below the threshold, otherwise False.
        """
        return gpa < threshold

    def get_class_average(self, subject_id: int) -> float:
        """Calculates the average numerical score for a specific subject.
        
        Args:
            subject_id (int): The unique ID of the target subject.
            
        Returns:
            float: The class average score, rounded to two decimals.
        """
        query = "SELECT score FROM grades WHERE subject_id = ?"
        rows = self.db._fetch_all(query, (subject_id,))
        scores = [row[0] for row in rows if row[0] is not None]
        
        if not scores:
            return 0.0
            
        return round(sum(scores) / len(scores), 2)

    def get_top_students(self, n: int = 5) -> list:
        """Retrieves the top performing students mapped by average score.
        
        Args:
            n (int, optional): The number of top students to return. Defaults to 5.
            
        Returns:
            list: A ranked array of student record dictionaries.
        """
        query = '''
            SELECT u.name, u.username, s.department, AVG(g.score) as avg_score
            FROM students s
            JOIN users u ON s.user_id = u.id
            JOIN grades g ON g.student_id = s.id
            GROUP BY s.id
            ORDER BY avg_score DESC
            LIMIT ?
        '''
        rows = self.db._fetch_all(query, (n,))
        
        return [
            {
                "name": row[0],
                "username": row[1],
                "department": row[2],
                "average_score": round(row[3], 2) if row[3] else 0.0
            }
            for row in rows
        ]

    @staticmethod
    def get_grade_summary(grades: list) -> dict:
        """Computes a statistical summary of a student's grade records.
        
        Args:
            grades (list): A list of grade tuples representing database records.
            
        Returns:
            dict: An aggregated summary containing highest, lowest, average scores, counts, and performance label.
        """
        if not grades:
            return {
                "highest_score": 0.0,
                "lowest_score": 0.0,
                "average_score": 0.0,
                "total_subjects": 0,
                "passed_subjects": 0,
                "failed_subjects": 0,
                "performance_label": "No Data"
            }
            
        valid_scores = [g[3] for g in grades if len(g) > 3 and g[3] is not None]
        
        if not valid_scores:
            return {
                "highest_score": 0.0,
                "lowest_score": 0.0,
                "average_score": 0.0,
                "total_subjects": 0,
                "passed_subjects": 0,
                "failed_subjects": 0,
                "performance_label": "No Data"
            }
            
        highest = max(valid_scores)
        lowest = min(valid_scores)
        avg = round(sum(valid_scores) / len(valid_scores), 2)
        total = len(valid_scores)
        passed = sum(1 for s in valid_scores if GradeService.letter_grade(s) != 'F')
        failed = total - passed
        
        gpa = GradeService.calculate_gpa(valid_scores)
        if gpa >= 3.5:
            label = "Excellent"
        elif gpa >= 3.0:
            label = "Good"
        elif gpa >= 2.0:
            label = "Average"
        else:
            label = "Poor"
            
        return {
            "highest_score": highest,
            "lowest_score": lowest,
            "average_score": avg,
            "total_subjects": total,
            "passed_subjects": passed,
            "failed_subjects": failed,
            "performance_label": label
        }

    @staticmethod
    def get_subject_ranking(grades: list) -> list:
        """Sorts a list of grade records into a ranking from highest to lowest score.
        
        Args:
            grades (list): A list of grade tuples from the database.
            
        Returns:
            list: A sorted list of (subject_name, score, letter) tuples.
        """
        valid_grades = [g for g in grades if len(g) > 4 and g[3] is not None]
        sorted_grades = sorted(valid_grades, key=lambda x: x[3], reverse=True)
        return [(g[1], g[3], g[4]) for g in sorted_grades]
