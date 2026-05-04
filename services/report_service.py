"""
Service for generating performance charts and reports.
"""

class ReportService:
    """Handles visual report generation for student performance.
    
    This class demonstrates encapsulation by grouping related reporting behaviors.
    """
    @staticmethod
    def generate_performance_chart(student_id: int, grades: list[float]):
        """Generates a chart of a student's grades.
        
        Args:
            student_id (int): The student's ID.
            grades (list[float]): The student's numerical grades.
            
        Returns:
            None: Implementation pending.
        """
        pass

    @staticmethod
    def generate_text_report(student, grades: list) -> str:
        """Generates a rich text report string for a student.
        
        Args:
            student: The Student model instance.
            grades (list): A list of grade tuples from the database.
            
        Returns:
            str: A formatted multiline text string summarizing performance.
        """
        from services.grade_service import GradeService
        
        summary = GradeService.get_grade_summary(grades)
        ranking = GradeService.get_subject_ranking(grades)
        
        gpa = student.gpa if hasattr(student, 'gpa') else 0.0
        
        if gpa >= 3.5:
            rec = "Outstanding performance. Keep it up."
        elif gpa >= 3.0:
            rec = "Good standing. Push for excellence."
        elif gpa >= 2.0:
            rec = "Satisfactory. Focus on weaker subjects."
        else:
            rec = "Academic support recommended immediately."
            
        report = []
        report.append(f"Student: {student.name}")
        report.append(f"Department: {student.department} | Semester: {student.semester}")
        report.append("-" * 40)
        report.append(f"Cumulative GPA: {gpa:.2f} ({summary['performance_label']})")
        report.append(f"Highest Score: {summary['highest_score']} | Lowest Score: {summary['lowest_score']}")
        report.append(f"Average Score: {summary['average_score']}")
        report.append(f"Subjects Tracked: {summary['total_subjects']} | Passed: {summary['passed_subjects']} | Failed: {summary['failed_subjects']}")
        report.append("-" * 40)
        report.append("Subject Ranking (Highest to Lowest):")
        
        if ranking:
            for i, (subj, score, letter) in enumerate(ranking, 1):
                report.append(f"  {i}. {subj}: {score} ({letter})")
        else:
            report.append("  No grades recorded.")
            
        report.append("-" * 40)
        report.append(f"Recommendation: {rec}")
        
        return "\n".join(report)
