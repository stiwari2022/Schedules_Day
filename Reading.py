import csv
import pandas as pd
import random
from fpdf import FPDF
import zipfile
import os

# Function to read CSV file and return data in required format
def read_csv_to_list(file_path):
    data = []
    
    # Open the CSV file
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        csvreader = csv.reader(csvfile)
        
        # Skip the header row
        next(csvreader)
        
        # Iterate through the rows
        for row in csvreader:
            # Extract the timestamp, name, and subjects
            timestamp = row[0]
            name = row[1]
            subjects = row[2:]
            
            # Calculate the number of subjects
            subject_count = len(subjects)
            
            # Append the row in the required format
            data.append([timestamp, name, subject_count] + subjects)
    
    return data

# Assign classes based on preferences, grade, and timestamp
def assign_classes(students, class_capacities, max_classes):
    # Sort students by grade (descending), then by timestamp (ascending)
    students = sorted(students, key=lambda x: (-x['grade'], x['timestamp']))
    
    assignments = {student['name']: [] for student in students}

    # Temp dictionary for class capacities, to track available spots
    temp_class_capacities = class_capacities.copy()
    
    for student in students:
        preferences = student['preferences']
        assigned = []
        
        # Assign by preference
        for pref in preferences:
            if temp_class_capacities.get(pref, 0) > 0:
                assigned.append(pref)
                temp_class_capacities[pref] -= 1
            if len(assigned) == max_classes:  # Only assign up to max_classes
                break
        
        # Random classes if less than max_classes are assgned
        while len(assigned) < max_classes:
            available_classes = [cls for cls, cap in temp_class_capacities.items() if cap > 0]
            if available_classes:
                rand_class = random.choice(available_classes)
                assigned.append(rand_class)
                temp_class_capacities[rand_class] -= 1
        
        assignments[student['name']] = assigned
    
    return assignments

# Generate PDF schedules for each student
def generate_pdf_schedule(assignments, output_dir="schedules"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for student, classes in assignments.items():
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        pdf.cell(200, 10, txt=f"Schedule for {student}", ln=True, align="C")
        pdf.ln(10)  # Line break
        
        for i, cls in enumerate(classes, 1):
            pdf.cell(200, 10, txt=f"Class {i}: {cls}", ln=True, align="L")
        
        # Save PDF for each student
        pdf_file = os.path.join(output_dir, f"{student}_schedule.pdf")
        pdf.output(pdf_file)
        print(f"Generated schedule for {student}: {pdf_file}")

# Pckange all PDFs into a ZIP file
def package_pdfs_to_zip(output_dir="schedules", zip_filename="schedules.zip"):
    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        # Add all PDF files in the output directory to the zip file
        for root, _, files in os.walk(output_dir):
            for file in files:
                if file.endswith(".pdf"):
                    zipf.write(os.path.join(root, file), file)
    
    print(f"Packaged all schedules into: {zip_filename}")
    return zip_filename

# Main function to run the process
def main(file_path, class_capacities, max_classes):
    # Read student data from CSV
    data = read_csv_to_list(file_path)
    
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
            'preferences': preferences
        })

    # Assing classes based on preferences, grade, and timestamp
    assignments = assign_classes(students, class_capacities, max_classes)

    # Make PDF schedules for each student
    generate_pdf_schedule(assignments)

    # Package all PDFs into a ZIP file for download
    zip_file = package_pdfs_to_zip()

    # Auto download
    print(f"Download the file: {zip_file}")

if __name__ == "__main__":
    # YOU SHOULD change these values to any other class capacities or maximum number of classes
    class_capacities = {"Math": 3, "English": 3, "History": 3, "CS": 3, "Chem": 3}
    max_classes = 1  # Keep at 1 for seminar day
    file_path = 'data.csv'  # Change name of csv to data.csv
    
    main(file_path, class_capacities, max_classes)
