import csv
import pandas as pd
import random
from fpdf import FPDF
import zipfile
import os



max_classes = 3 #Max amount of classes student can have in a day
cap = 5 #Max amount of students in each class
lunch = True  #Set this to True if you want to assign lunch periods
student_file_path = 'data.csv'  #Student preferences CSV
classes_file_path = 'classes.csv'  #Classes CSV



#Reading the classes and get capacities
def read_classes_from_csv(file_path, cap):
    class_capacities = {}
    with open(file_path, newline='', encoding='utf-8') as csvfile: #Open the CSV file
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            classes = row
            for cls in classes:
                class_capacities[cls] = cap
    return class_capacities

#Reading CSV file and return student data
def read_csv_to_list(file_path):
    data = []
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        csvreader = csv.reader(csvfile)
        next(csvreader)
        for row in csvreader:
            timestamp = row[0]
            name = row[1]
            subjects = row[2:]
            subject_count = len(subjects)
            data.append([timestamp, name, subject_count] + subjects)
    return data

#Give classes based on preferences, grade, and timestamp
def assign_classes(students, class_capacities, max_classes, lunch=False):
    #Sort students by grade (descending), then by timestamp (ascending)
    students = sorted(students, key=lambda x: (-x['grade'], x['timestamp']))
    assignments = {student['name']: [] for student in students}
    #Temp dict for class capacities, to track open spots
    temp_class_capacities = class_capacities.copy()
    for idx, student in enumerate(students):
        preferences = student['preferences']
        assigned = []

        #Assign by pref
        for pref in preferences:
            if temp_class_capacities.get(pref, 0) > 0:
                assigned.append(pref)
                temp_class_capacities[pref] -= 1
            if len(assigned) == max_classes:
                break
    
        #Rando classes if less than max_classes are assigned
        while len(assigned) < max_classes:
            available_classes = [cls for cls, cap in temp_class_capacities.items() if cap > 0]
            if available_classes:
                rand_class = random.choice(available_classes)
                assigned.append(rand_class)
                temp_class_capacities[rand_class] -= 1

        #Lunch period if lunch variable is set to True
        if lunch:
            if idx % 2 == 0:  # Assign half to have lunch before the last two periods
                assigned.insert(-2, "Lunch")
            else:  # Assign the other half to have lunch just before the last period
                assigned.insert(-1, "Lunch")
        assignments[student['name']] = assigned
    return assignments

#Make PDF schedules for each student
def generate_pdf_schedule(assignments, output_dir="schedules"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    for student, classes in assignments.items():
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Schedule for {student}", ln=True, align="C")
        pdf.ln(10)
        for i, cls in enumerate(classes, 1):
            pdf.cell(200, 10, txt=f"Class {i}: {cls}", ln=True, align="L")

        #Save PDFs for each student
        pdf_file = os.path.join(output_dir, f"{student}_schedule.pdf")
        pdf.output(pdf_file)
        print(f"Generated schedule for {student}: {pdf_file}")

#Package PDFs into ZIP file
def package_pdfs_to_zip(output_dir="schedules", zip_filename="schedules.zip"):
    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        #Put alll PDF files in the outputting directory to the zip file
        for root, _, files in os.walk(output_dir):
            for file in files:
                if file.endswith(".pdf"):
                    zipf.write(os.path.join(root, file), file)
    print(f"Packaged all schedules into: {zip_filename}")
    return zip_filename

# Main function to run the process
def main(student_file_path, classes_file_path, cap, max_classes, lunch):
    #Classes from CSV
    class_capacities = read_classes_from_csv(classes_file_path, cap)
    #Reading student data from CSV
    data = read_csv_to_list(student_file_path)
    students = []
    for row in data:
        timestamp = pd.to_datetime(row[0])
        name = row[1]
        grade = int(row[2])
        preferences = row[3:]
        students.append({
            'timestamp': timestamp,
            'name': name,
            'grade': grade,
            'preferences': preferences })

    #Give classes based on PREFERENCES, GRADE, then TIMESTAMP
    assignments = assign_classes(students, class_capacities, max_classes, lunch)

    #Make PDF schedules for each student
    generate_pdf_schedule(assignments)

    #Package PDFs into ZIP file for downloading
    zip_file = package_pdfs_to_zip()

    print(f"Download the file: {zip_file}")

if __name__ == "__main__":
    main(student_file_path, classes_file_path, cap, max_classes, lunch)
