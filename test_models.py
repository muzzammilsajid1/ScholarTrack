"""
Standalone test script to demonstrate Object-Oriented Programming (OOP) concepts
implemented in the ScholarTrack system. Run this during the viva presentation.
"""
from models.student import Student
from models.teacher import Teacher
from models.admin import Admin
from services.grade_service import GradeService
from models.exceptions import InvalidGradeError

def run_tests():
    print("=" * 60)
    print("SCHOLARTRACK OOP CONCEPTS DEMONSTRATION")
    print("=" * 60)
    
    print("\n[+] Creating Instances (Instantiation)...")
    student = Student(student_id=1, name="Alice Smith", username="alice_s", semester=2, department="Computer Science")
    teacher = Teacher(teacher_id=2, name="Dr. Bob Jones", username="bjones", department="Computer Science")
    admin = Admin(admin_id=3, name="System Admin", username="admin", access_level=3)
    
    print("Successfully created Student, Teacher, and Admin native instances.")

    # ---------------------------------------------------------
    # 1. ENCAPSULATION
    # ---------------------------------------------------------
    print("\n" + "-" * 60)
    print("1. ENCAPSULATION")
    print("-" * 60)
    print("Attempting to bypass @property setter constraints by setting student.gpa = 5.0...")
    
    try:
        student.gpa = 5.0
        print("FAIL: The GPA was improperly configured to 5.0 (Constraints bypassed).")
    except InvalidGradeError as e:
        print(f"SUCCESS: Encapsulation successfully blocked invalid assignment!\nCaught InvalidGradeError -> {e}")

    # ---------------------------------------------------------
    # 2. POLYMORPHISM
    # ---------------------------------------------------------
    print("\n" + "-" * 60)
    print("2. POLYMORPHISM")
    print("-" * 60)
    print("Iterating through a polymorphic array of different User schemas calling generate_report() on each without knowing their exact types:\n")
    
    users = [student, teacher, admin]
    for user in users:
        print(f">>> Invoking generate_report() automatically routed to {user.__class__.__name__} Class:")
        print(user.generate_report())
        print()

    # ---------------------------------------------------------
    # 3. INHERITANCE
    # ---------------------------------------------------------
    print("-" * 60)
    print("3. INHERITANCE")
    print("-" * 60)
    print("Displaying the Method Resolution Order (MRO) hierarchy dynamically utilizing reflection to prove structural subclassing behavior:\n")
    
    mro = [cls.__name__ for cls in type(student).__mro__]
    print(" -> ".join(mro))
    print("\n(Note how Student dynamically inherits from User natively, routing back to ABC natively.)")

    # ---------------------------------------------------------
    # 4. GRADESERVICE (@staticmethod usage)
    # ---------------------------------------------------------
    print("\n" + "-" * 60)
    print("4. GRADE SERVICE (@staticmethod Usage)")
    print("-" * 60)
    print("Executing standalone GPA mappings independent of instance creation overhead:")
    
    sample_scores = [95.0, 85.0, 75.0, 65.0]
    print(f"Feeding raw scores: {sample_scores}")
    
    gpa = GradeService.calculate_gpa(sample_scores)
    print(f"GradeService explicitly calculated Cumulative GPA => {gpa}")
    
    is_risk = GradeService.is_at_risk(gpa)
    print(f"GradeService verified risk thresholds => Is student at risk? {is_risk}")

    print("\n" + "=" * 60)
    print("END OF VIVA PRESENTATION SCRIPT")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
