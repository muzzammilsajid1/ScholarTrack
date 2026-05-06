# Service for generating performance charts and reports.

class ReportService:
    def __init__(self):
        pass

    def generate_performance_chart(self, student_id, grades):
        pass

    def generate_text_report(self, student, grades):
        from services.grade_service import GradeService
        
        gs = GradeService(None)
        summary = gs.get_grade_summary(grades)
        ranking = gs.get_subject_ranking(grades)
        
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
