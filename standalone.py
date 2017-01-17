#!/usr/bin/env python
#

from __future__ import print_function
import os
import csv
import sys
import re


from jinja2 import Template

from munkres import Munkres


def PadJobRankingsData(job_rankings):
    maximum_rank = 999999
    cost_matrix = []
    for row in job_rankings:
        new_row = row
        for cell_index in range(len(new_row)):
            cell_value = row[cell_index]
            if cell_value == '' or cell_value == '0':
                cell_value = str(maximum_rank * 2)
            new_row[cell_index] = int(cell_value)
        cost_matrix.append(new_row)
    return cost_matrix


def BestJobFit(job_rankings, student_ids, job_ids):
    # Using the excellent munkres module (http://bmc.github.com/munkres/).
    #from munkres import Munkres
    m = Munkres()
    indexes = m.compute(job_rankings)
    bestfit_array = []
    for row, column in indexes:
        student_id = student_ids[row]
        job_id = job_ids[column]
        value = job_rankings[row][column]
        bestfit_array.append({'student_id': student_id, 'job_id': job_id, 'ranking': value})
    return bestfit_array


def ProcessCSVFile(csv_file):
    path = os.path.join(os.path.dirname(__file__), 'results.html')
    template = Template(open(path).read())

    with open(csv_file, 'r') as f:
        source_matrix = list(csv.reader(f, delimiter=',', quotechar='"'))

    column_headings_row_index = 1
    data_start_row_index = 2

    column_headings_row = source_matrix[column_headings_row_index]
    # Find student ID column
    studentid_column_heading = re.compile("Name")
    studentid_column_index = -1
    for column_index in range(len(column_headings_row)):
        column_heading = column_headings_row[column_index]
        if studentid_column_heading.search(column_heading):
            studentid_column_index = column_index
    if studentid_column_index < 0:
        # Couldn't find a student ID Column, freak out or something
        print("FREAK OUT - No student ID Column")
    # Extract the student IDs
    student_ids = []
    for row in source_matrix[data_start_row_index:]:
        student_ids.append(row[studentid_column_index])
    # Make sure there are no duplicate student IDs - (OPTIONAL)
    if HasDuplicates(student_ids):
        # Freak out
        print("FREAK OUT - Duplicate student IDs")
    job_ids = []
    job_column_indices = []
    job_column_heading = re.compile("-(.*?)\s*-Rank")
    for column_heading_index in range(len(column_headings_row)):
        column_heading = column_headings_row[column_heading_index]
        if job_column_heading.search(column_heading):
            job_column_indices.append(column_heading_index)
            # Strip leading "-" and trailing "-Rank" from job ID
            job_id = job_column_heading.search(column_heading).group(1)
            job_ids.append(job_id)
    # Extract sub-table of data from matrix
    job_rankings = []
    for row_index in range(data_start_row_index,len(student_ids)+data_start_row_index):
        source_row = source_matrix[row_index]
        rankings_row = []
        for column_index in job_column_indices:
           rankings_row.append(source_row[column_index])
        job_rankings.append(rankings_row)
    # Process data
    # Replace 0 and blank values in matrix with maximal values
    job_rankings = PadJobRankingsData(job_rankings)
    # Perform calculation
    job_matches = BestJobFit(job_rankings, student_ids, job_ids)
    # Render in the template specified by path
    template_values = { 'student_ids': student_ids,
                        'job_ids': job_ids,
                        'job_rankings': job_rankings,
                        'matches': job_matches }
    with open('output.html', 'w') as f:
        html_output = template.render(template_values)
        f.write(html_output)


def HasDuplicates(some_array):
    # HasDuplicates(some_array): determines whether any
    # values in the given array are duplicates.
    #
    # Unit tests:
    # HasDuplicates(["a", "aa", "aaa", "aaaa", "a"]) = True
    # HasDuplicates(["a", "aa", "aaa", "aaaa"]) = False
    # HasDuplicates([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]) = False
    # HasDuplicates([1, 2, 3, 1]) = True
    for array_value in some_array:
        if some_array.count(array_value) > 1:
            return True
    return False


def main():
    if(len(sys.argv)) > 1:
        csv_filename = sys.argv[1]
    else:
        print("Usage:")
        print("{0} csv_filename.csv".format(__file__))
        sys.exit(1)
    # else:
    #     csv_filename = 'raw_data_for_matching.csv'
    
    ProcessCSVFile(csv_filename)

if __name__ == '__main__':
    main()
