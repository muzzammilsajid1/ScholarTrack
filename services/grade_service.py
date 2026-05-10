# Provides business logic for calculating grades, GPAs, and class rankings
# Encapsulation: groups all grading algorithms into a single stateless service class
# Abstraction: hides complex aggregation rules behind simple method calls

class GradeService:
    def __init__(self, db):
        self.db = db

    # Centralize grade threshold definitions to ensure consistency across all views
    def letter_grade(self, score):
        if not (0 <= score <= 100):
            print(f"Error: Score {score} is out of range. Must be between 0 and 100 inclusive.")
            return None
            
        if score >= 90: return 'A'
        elif score >= 80: return 'B'
        elif score >= 70: return 'C'
        elif score >= 60: return 'D'
        else: return 'F'

    # Convert numeric scores to GPA scale points before averaging to match university standards
    def calculate_gpa(self, scores):
        if not scores:
            return 0.0
            
        gpa_scale_map = {'A': 4.0, 'B': 3.0, 'C': 2.0, 'D': 1.0, 'F': 0.0}
        
        total_points = 0.0
        for score in scores:
            letter = self.letter_grade(score)
            total_points += gpa_scale_map[letter]
            
        return round(total_points / len(scores), 2)

    def is_at_risk(self, gpa, threshold=2.0):
        return gpa < threshold

