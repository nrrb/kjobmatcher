#!/usr/bin/env python
#

import os
import urllib
import csv
import sys
import re

from google.appengine.ext import blobstore
from google.appengine.ext import webapp
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

class MainHandler(webapp.RequestHandler):
    def get(self):
        upload_url = blobstore.create_upload_url('/upload')
        template_values = {'upload_url': upload_url }
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, template_values))

class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        upload_files = self.get_uploads('file')  # 'file' is file upload field in the form
        blob_info = upload_files[0]
        self.redirect('/serve/%s' % blob_info.key())

class ServeHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, resource):
        resource = str(urllib.unquote(resource))
        blob_reader = blobstore.BlobReader(resource)
        blob_info = blobstore.BlobInfo.get(resource)
#        self.send_blob(blob_info)
        self.ProcessCSVFile(blob_reader)
    def PadJobRankingsData(self, job_rankings):
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
    def BestJobFit(self, job_rankings, student_ids, job_ids):
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
    def ProcessCSVFile(self, csv_file):
        path = os.path.join(os.path.dirname(__file__), 'results.html')
        source_data_rows = csv.reader(csv_file, delimiter=',', quotechar='"')
        source_matrix = []
        column_headings_row_index = 1
        data_start_row_index = 2
        for row in source_data_rows:
            source_matrix.append(row)
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
            self.response.out.write("FREAK OUT - No student ID Column")
        # Extract the student IDs
        student_ids = []
        for row in source_matrix[data_start_row_index:]:
            student_ids.append(row[studentid_column_index])
        # Make sure there are no duplicate student IDs - (OPTIONAL)
        if self.HasDuplicates(student_ids):
            # Freak out
            self.response.out.write("FREAK OUT - Duplicate student IDs")
        # Identify Job IDs and respective column indices
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
        job_rankings = self.PadJobRankingsData(job_rankings)
        # Perform calculation
        job_matches = self.BestJobFit(job_rankings, student_ids, job_ids)
        # Render in the template specified by path
        template_values = { 'student_ids': student_ids,
                            'job_ids': job_ids,
                            'job_rankings': job_rankings,
                            'matches': job_matches }
        self.response.out.write(template.render(path, template_values))        
    def HasDuplicates(self, some_array):
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

#############################################################################
# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

__all__     = ['Munkres', 'make_cost_matrix']

# ---------------------------------------------------------------------------
# Globals
# ---------------------------------------------------------------------------

# Info about the module
__version__   = "1.0.5.4"
__author__    = "Brian Clapper, bmc@clapper.org"
__url__       = "http://bmc.github.com/munkres/"
__copyright__ = "(c) 2008 Brian M. Clapper"
__license__   = "BSD-style license"

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------

class Munkres:
    """
    Calculate the Munkres solution to the classical assignment problem.
    See the module documentation for usage.
    """

    def __init__(self):
        """Create a new instance"""
        self.C = None
        self.row_covered = []
        self.col_covered = []
        self.n = 0
        self.Z0_r = 0
        self.Z0_c = 0
        self.marked = None
        self.path = None

    def make_cost_matrix(profit_matrix, inversion_function):
        """
        **DEPRECATED**

        Please use the module function ``make_cost_matrix()``.
        """
        import munkres
        return munkres.make_cost_matrix(profit_matrix, inversion_function)

    make_cost_matrix = staticmethod(make_cost_matrix)

    def pad_matrix(self, matrix, pad_value=0):
        """
        Pad a possibly non-square matrix to make it square.

        :Parameters:
            matrix : list of lists
                matrix to pad

            pad_value : int
                value to use to pad the matrix

        :rtype: list of lists
        :return: a new, possibly padded, matrix
        """
        max_columns = 0
        total_rows = len(matrix)

        for row in matrix:
            max_columns = max(max_columns, len(row))

        total_rows = max(max_columns, total_rows)

        new_matrix = []
        for row in matrix:
            row_len = len(row)
            new_row = row[:]
            if total_rows > row_len:
                # Row too short. Pad it.
                new_row += [0] * (total_rows - row_len)
            new_matrix += [new_row]

        while len(new_matrix) < total_rows:
            new_matrix += [[0] * total_rows]

        return new_matrix

    def compute(self, cost_matrix):
        """
        Compute the indexes for the lowest-cost pairings between rows and
        columns in the database. Returns a list of (row, column) tuples
        that can be used to traverse the matrix.

        :Parameters:
            cost_matrix : list of lists
                The cost matrix. If this cost matrix is not square, it
                will be padded with zeros, via a call to ``pad_matrix()``.
                (This method does *not* modify the caller's matrix. It
                operates on a copy of the matrix.)

                **WARNING**: This code handles square and rectangular
                matrices. It does *not* handle irregular matrices.

        :rtype: list
        :return: A list of ``(row, column)`` tuples that describe the lowest
                 cost path through the matrix

        """
        self.C = self.pad_matrix(cost_matrix)
        self.n = len(self.C)
        self.original_length = len(cost_matrix)
        self.original_width = len(cost_matrix[0])
        self.row_covered = [False for i in range(self.n)]
        self.col_covered = [False for i in range(self.n)]
        self.Z0_r = 0
        self.Z0_c = 0
        self.path = self.__make_matrix(self.n * 2, 0)
        self.marked = self.__make_matrix(self.n, 0)

        done = False
        step = 1

        steps = { 1 : self.__step1,
                  2 : self.__step2,
                  3 : self.__step3,
                  4 : self.__step4,
                  5 : self.__step5,
                  6 : self.__step6 }

        while not done:
            try:
                func = steps[step]
                step = func()
            except KeyError:
                done = True

        # Look for the starred columns
        results = []
        for i in range(self.original_length):
            for j in range(self.original_width):
                if self.marked[i][j] == 1:
                    results += [(i, j)]

        return results

    def __copy_matrix(self, matrix):
        """Return an exact copy of the supplied matrix"""
        return copy.deepcopy(matrix)

    def __make_matrix(self, n, val):
        """Create an *n*x*n* matrix, populating it with the specific value."""
        matrix = []
        for i in range(n):
            matrix += [[val for j in range(n)]]
        return matrix

    def __step1(self):
        """
        For each row of the matrix, find the smallest element and
        subtract it from every element in its row. Go to Step 2.
        """
        C = self.C
        n = self.n
        for i in range(n):
            minval = min(self.C[i])
            # Find the minimum value for this row and subtract that minimum
            # from every element in the row.
            for j in range(n):
                self.C[i][j] -= minval

        return 2

    def __step2(self):
        """
        Find a zero (Z) in the resulting matrix. If there is no starred
        zero in its row or column, star Z. Repeat for each element in the
        matrix. Go to Step 3.
        """
        n = self.n
        for i in range(n):
            for j in range(n):
                if (self.C[i][j] == 0) and \
                   (not self.col_covered[j]) and \
                   (not self.row_covered[i]):
                    self.marked[i][j] = 1
                    self.col_covered[j] = True
                    self.row_covered[i] = True

        self.__clear_covers()
        return 3

    def __step3(self):
        """
        Cover each column containing a starred zero. If K columns are
        covered, the starred zeros describe a complete set of unique
        assignments. In this case, Go to DONE, otherwise, Go to Step 4.
        """
        n = self.n
        count = 0
        for i in range(n):
            for j in range(n):
                if self.marked[i][j] == 1:
                    self.col_covered[j] = True
                    count += 1

        if count >= n:
            step = 7 # done
        else:
            step = 4

        return step

    def __step4(self):
        """
        Find a noncovered zero and prime it. If there is no starred zero
        in the row containing this primed zero, Go to Step 5. Otherwise,
        cover this row and uncover the column containing the starred
        zero. Continue in this manner until there are no uncovered zeros
        left. Save the smallest uncovered value and Go to Step 6.
        """
        step = 0
        done = False
        row = -1
        col = -1
        star_col = -1
        while not done:
            (row, col) = self.__find_a_zero()
            if row < 0:
                done = True
                step = 6
            else:
                self.marked[row][col] = 2
                star_col = self.__find_star_in_row(row)
                if star_col >= 0:
                    col = star_col
                    self.row_covered[row] = True
                    self.col_covered[col] = False
                else:
                    done = True
                    self.Z0_r = row
                    self.Z0_c = col
                    step = 5

        return step

    def __step5(self):
        """
        Construct a series of alternating primed and starred zeros as
        follows. Let Z0 represent the uncovered primed zero found in Step 4.
        Let Z1 denote the starred zero in the column of Z0 (if any).
        Let Z2 denote the primed zero in the row of Z1 (there will always
        be one). Continue until the series terminates at a primed zero
        that has no starred zero in its column. Unstar each starred zero
        of the series, star each primed zero of the series, erase all
        primes and uncover every line in the matrix. Return to Step 3
        """
        count = 0
        path = self.path
        path[count][0] = self.Z0_r
        path[count][1] = self.Z0_c
        done = False
        while not done:
            row = self.__find_star_in_col(path[count][1])
            if row >= 0:
                count += 1
                path[count][0] = row
                path[count][1] = path[count-1][1]
            else:
                done = True

            if not done:
                col = self.__find_prime_in_row(path[count][0])
                count += 1
                path[count][0] = path[count-1][0]
                path[count][1] = col

        self.__convert_path(path, count)
        self.__clear_covers()
        self.__erase_primes()
        return 3

    def __step6(self):
        """
        Add the value found in Step 4 to every element of each covered
        row, and subtract it from every element of each uncovered column.
        Return to Step 4 without altering any stars, primes, or covered
        lines.
        """
        minval = self.__find_smallest()
        for i in range(self.n):
            for j in range(self.n):
                if self.row_covered[i]:
                    self.C[i][j] += minval
                if not self.col_covered[j]:
                    self.C[i][j] -= minval
        return 4

    def __find_smallest(self):
        """Find the smallest uncovered value in the matrix."""
        minval = sys.maxint
        for i in range(self.n):
            for j in range(self.n):
                if (not self.row_covered[i]) and (not self.col_covered[j]):
                    if minval > self.C[i][j]:
                        minval = self.C[i][j]
        return minval

    def __find_a_zero(self):
        """Find the first uncovered element with value 0"""
        row = -1
        col = -1
        i = 0
        n = self.n
        done = False

        while not done:
            j = 0
            while True:
                if (self.C[i][j] == 0) and \
                   (not self.row_covered[i]) and \
                   (not self.col_covered[j]):
                    row = i
                    col = j
                    done = True
                j += 1
                if j >= n:
                    break
            i += 1
            if i >= n:
                done = True

        return (row, col)

    def __find_star_in_row(self, row):
        """
        Find the first starred element in the specified row. Returns
        the column index, or -1 if no starred element was found.
        """
        col = -1
        for j in range(self.n):
            if self.marked[row][j] == 1:
                col = j
                break

        return col

    def __find_star_in_col(self, col):
        """
        Find the first starred element in the specified row. Returns
        the row index, or -1 if no starred element was found.
        """
        row = -1
        for i in range(self.n):
            if self.marked[i][col] == 1:
                row = i
                break

        return row

    def __find_prime_in_row(self, row):
        """
        Find the first prime element in the specified row. Returns
        the column index, or -1 if no starred element was found.
        """
        col = -1
        for j in range(self.n):
            if self.marked[row][j] == 2:
                col = j
                break

        return col

    def __convert_path(self, path, count):
        for i in range(count+1):
            if self.marked[path[i][0]][path[i][1]] == 1:
                self.marked[path[i][0]][path[i][1]] = 0
            else:
                self.marked[path[i][0]][path[i][1]] = 1

    def __clear_covers(self):
        """Clear all covered matrix cells"""
        for i in range(self.n):
            self.row_covered[i] = False
            self.col_covered[i] = False

    def __erase_primes(self):
        """Erase all prime markings"""
        for i in range(self.n):
            for j in range(self.n):
                if self.marked[i][j] == 2:
                    self.marked[i][j] = 0

# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------

def make_cost_matrix(profit_matrix, inversion_function):
    """
    Create a cost matrix from a profit matrix by calling
    'inversion_function' to invert each value. The inversion
    function must take one numeric argument (of any type) and return
    another numeric argument which is presumed to be the cost inverse
    of the original profit.

    This is a static method. Call it like this:

    .. python::

        cost_matrix = Munkres.make_cost_matrix(matrix, inversion_func)

    For example:

    .. python::

        cost_matrix = Munkres.make_cost_matrix(matrix, lambda x : sys.maxint - x)

    :Parameters:
        profit_matrix : list of lists
            The matrix to convert from a profit to a cost matrix

        inversion_function : function
            The function to use to invert each entry in the profit matrix

    :rtype: list of lists
    :return: The converted matrix
    """
    cost_matrix = []
    for row in profit_matrix:
        cost_matrix.append([inversion_function(value) for value in row])
    return cost_matrix

def print_matrix(matrix, msg=None):
    """
    Convenience function: Displays the contents of a matrix of integers.

    :Parameters:
        matrix : list of lists
            Matrix to print

        msg : str
            Optional message to print before displaying the matrix
    """
    import math

    if msg is not None:
        print msg

    # Calculate the appropriate format width.
    width = 0
    for row in matrix:
        for val in row:
            width = max(width, int(math.log10(val)) + 1)

    # Make the format string
    format = '%%%dd' % width

    # Print the matrix
    for row in matrix:
        sep = '['
        for val in row:
            sys.stdout.write(sep + format % val)
            sep = ', '
        sys.stdout.write(']\n')
#############################################################################

def main():
    sys.path.insert(0, '.')
    application = webapp.WSGIApplication(
          [('/', MainHandler),
           ('/upload', UploadHandler),
           ('/serve/([^/]+)?', ServeHandler),
          ], debug=True)
    run_wsgi_app(application)

if __name__ == '__main__':
  main()
