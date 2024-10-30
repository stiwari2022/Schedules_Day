import csv
import pandas as pd
import random
from fpdf import FPDF
import zipfile
import os

max_classes = 3  # Max amount of classes student can have in a day
cap = 5  # Max amount of students in each class
lunch = True  # Set this to True if you want to assign lunch periods
student_file_path = 'data.csv'  # Student preferences CSV
classes_file_path = 'classes.csv'  # Classes CSV

# Reading the classes and get capacities
def read_classes_from_csv(file_path, cap):
    class_capacities = {}
    with open(file_path, newline='', encoding='utf-8') as csvfile:  # Open the CSV file
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            classes = row
            for cls in classes:
                class_capacities[cls] = cap
    return class_capacities

# Reading CSV file and return student data
def read_csv_to_list(file_path):
    data = []
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        csvreader = csv.reader(csvfile)
        next(csvreader)  # Skip header
        for row in csvreader:
            timestamp = row[0]
            name = row[1]
            email = row[2]
            grade = row[3]  # Capture grade from the row
            subjects = row[4:]
            subject_count = len(subjects)
            data.append([timestamp, name, email, grade, subject_count] + subjects)
    return data

# Assign classes based on preferences, grade, and timestamp
def assign_classes(students, class_capacities, max_classes, lunch=False):
    # Sort students first by grade (descending), then by timestamp
    students = sorted(students, key=lambda x: (-int(x['grade']), x['timestamp']))
    assignments = {student['name']: [] for student in students}
    temp_class_capacities = class_capacities.copy()
    
    for idx, student in enumerate(students):
        preferences = student['preferences']
        assigned = []
        
        # Assign by preferences
        for pref in preferences:
            if temp_class_capacities.get(pref, 0) > 0:
                assigned.append(pref)
                temp_class_capacities[pref] -= 1
            if len(assigned) == max_classes:
                break
        
        # Random classes if less than max_classes are assigned
        while len(assigned) < max_classes:
            available_classes = [cls for cls, cap in temp_class_capacities.items() if cap > 0]
            if available_classes:
                rand_class = random.choice(available_classes)
                assigned.append(rand_class)
                temp_class_capacities[rand_class] -= 1

        # Lunch period if lunch variable is set to True
        if lunch:
            if idx % 2 == 0:
                assigned.insert(-2, "Lunch")
            else:
                assigned.insert(-1, "Lunch")
        
        assignments[student['name']] = (student['email'], assigned)
    return assignments

# Make PDF schedules for each student
def generate_pdf_schedule(assignments, output_dir="schedules"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    for student, (email, classes) in assignments.items():
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Schedule for {student} ({email})", ln=True, align="C")
        pdf.ln(10)
        for i, cls in enumerate(classes, 1):
            pdf.cell(200, 10, txt=f"Class {i}: {cls}", ln=True, align="L")

        # Save PDFs for each student
        pdf_file = os.path.join(output_dir, f"{student}_schedule.pdf")
        pdf.output(pdf_file)
        print(f"Generated schedule for {student}: {pdf_file}")

# Generate attendance list PDFs for each class
def generate_attendance_lists(assignments, output_dir="attendance"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Create attendance folder structure by class and period
    class_periods = {}
    for student, (_, classes) in assignments.items():
        for period, cls in enumerate(classes, 1):
            if cls not in class_periods:
                class_periods[cls] = {}
            if period not in class_periods[cls]:
                class_periods[cls][period] = []
            class_periods[cls][period].append(student)
    
    # Generate PDF attendance lists
    for cls, periods in class_periods.items():
        class_dir = os.path.join(output_dir, cls)
        if not os.path.exists(class_dir):
            os.makedirs(class_dir)
        
        for period, students in periods.items():
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt=f"Attendance List for {cls} - Period {period}", ln=True, align="C")
            pdf.ln(10)
            for student in students:
                pdf.cell(200, 10, txt=f"- {student}", ln=True, align="L")
            
            # Save attendance list PDF
            pdf_file = os.path.join(class_dir, f"Period_{period}_attendance.pdf")
            pdf.output(pdf_file)
            print(f"Generated attendance list for {cls} Period {period}: {pdf_file}")

# Package PDFs into ZIP file
def package_pdfs_to_zip(output_dir="schedules", zip_filename="schedules.zip"):
    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        for root, _, files in os.walk(output_dir):
            for file in files:
                if file.endswith(".pdf"):
                    zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), output_dir))
    print(f"Packaged all schedules into: {zip_filename}")
    return zip_filename

# Main function to run the process
def main(student_file_path, classes_file_path, cap, max_classes, lunch):
    # Classes from CSV
    class_capacities = read_classes_from_csv(classes_file_path, cap)
    # Reading student data from CSV
    data = read_csv_to_list(student_file_path)
    students = []
    for row in data:
        timestamp = pd.to_datetime(row[0])
        name = row[1]
        email = row[3]  # Change to grab email correctly from the row
        grade = int(row[2])  # Correctly capture the grade
        preferences = row[4:]  # Update index to capture subjects correctly
        students.append({
            'timestamp': timestamp,
            'name': name,
            'email': email,
            'grade': grade,
            'preferences': preferences
        })

    # Assign classes based on preferences, grade, then timestamp
    assignments = assign_classes(students, class_capacities, max_classes, lunch)

    # Make PDF schedules for each student
    generate_pdf_schedule(assignments)

    # Generate attendance lists by class and period
    generate_attendance_lists(assignments)

    # Package PDFs into ZIP file for downloading
    zip_file = package_pdfs_to_zip()

    print(f"Download the file: {zip_file}")

if __name__ == "__main__":
    main(student_file_path, classes_file_path, cap, max_classes, lunch)
