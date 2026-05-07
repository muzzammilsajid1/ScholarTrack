# Provides business logic for calculating grades, GPAs, and class rankings
# Encapsulation: groups all grading algorithms into a single stateless service class
# Abstraction: hides complex aggregation rules behind simple methods like get_class_average()
from storage.file_manager import FileManager

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

    # Aggregate grades from all enrolled students to compute the subject-wide performance
    def get_class_average(self, subject_id):
        enrolled = self.db.get_students_in_subject(subject_id)
        scores = []
        for student in enrolled:
            student_id = student[0]
            grades = self.db.get_student_grades(student_id)
            subject_info = {s[0]: s for s in self.db.get_subjects_for_student(student_id)}
            for g in grades:
                if len(g) < 4 or g[3] is None:
                    continue
                for s_id, subj in subject_info.items():
                    if s_id == subject_id and g[2] == subj[2]:
                        scores.append(g[3])
                        break

        if not scores:
            return 0.0
        return round(sum(scores) / len(scores), 2)

    # Sort students globally by their average score to identify top performers
    def get_top_students(self, n=5):
        all_students = self.db.get_all_students()
        ranked = []
        for student in all_students:
            student_id = student[0]
            grades = self.db.get_student_grades(student_id)
            scores = [g[3] for g in grades if len(g) >= 4 and g[3] is not None]
            avg = round(sum(scores) / len(scores), 2) if scores else 0.0
            ranked.append({
                "name": student[1],
                "username": student[2],
                "department": student[4],
                "average_score": avg,
            })

        ranked.sort(key=lambda x: x["average_score"], reverse=True)
        return ranked[:n]

    # Compute a quick snapshot of a student's standing for the dashboard
    def get_grade_summary(self, grades):
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
        passed = sum(1 for s in valid_scores if self.letter_grade(s) != 'F')
        failed = total - passed
        
        gpa = self.calculate_gpa(valid_scores)
        if gpa >= 3.5: label = "Excellent"
        elif gpa >= 3.0: label = "Good"
        elif gpa >= 2.0: label = "Average"
        else: label = "Poor"
            
        return {
            "highest_score": highest,
            "lowest_score": lowest,
            "average_score": avg,
            "total_subjects": total,
            "passed_subjects": passed,
            "failed_subjects": failed,
            "performance_label": label
        }

    # Order grades chronologically or by score so UI tables appear logical
    def get_subject_ranking(self, grades):
        valid_grades = [g for g in grades if len(g) > 4 and g[3] is not None]
        sorted_grades = sorted(valid_grades, key=lambda x: x[3], reverse=True)
        return [(g[1], g[3], g[4]) for g in sorted_grades]

