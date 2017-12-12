# Assuming Python 3
import csv
from io import StringIO
import re

class QualtricsKBFCSVImporter(object):

	def __init__(self, filename=None, csv_content_string=None, legacy_format=False):
		# Initial inputs
		self.filename = filename
		self.csv_content_string = csv_content_string
		self.legacy_format = legacy_format
		# 
		self.raw_data = list()
		self.raw_fieldnames = list()
		self.data = dict()
		self.respondents = list()
		self.organizations = list()
		# Variables used in the initial processing of the CSV data, not meant to be used after
		self.__header_row_index = None
		self.__data_start_row_index = None
		self.__organization_name_pattern = None
		self.__organizations_by_column_index = dict()
		# This is the alternate value provided in case there is no response in the file, e.g. ''. This will be 
		# parsed into an integer. This should represent a value larger than any of the actual values in the data.
		self.__NONRESPONSE_VALUE_TEXT = '99'
		self.__first_name_column_index = None
		self.__last_name_column_index = None

		if self.legacy_format:
			self.__header_row_index = 1
			self.__data_start_row_index = 2
			# Created regex using https://pythex.org/
			self.__organization_name_pattern = re.compile(r'-(?P<organization>.*)(?=-Rank)')
		else:
			self.__header_row_index = 1
			self.__data_start_row_index = 3
			# Created regex using https://pythex.org/
			self.__organization_name_pattern = re.compile(r'(?<=- Ranks - Preference - )(?P<organization>.*)(?= - Rank)')

		if self.filename:
			with open(self.filename, 'r') as f:
				self.raw_data = list(csv.reader(f))
		elif self.csv_content_string:
			self.raw_data = list(csv.reader(StringIO(self.csv_content_string)))

		# Extract column indices for the fields we care about, and extract organization names from the column headings they're embedded in
		self.raw_fieldnames = self.raw_data[self.__header_row_index]
		for column_index, field in enumerate(self.raw_fieldnames):
			if re.search(self.__organization_name_pattern, field):
				organization_name = re.search(self.__organization_name_pattern, field).groupdict()['organization']
				self.__organizations_by_column_index[organization_name] = column_index
				self.organizations.append(organization_name)
			elif 'First Name' in field:
				self.__first_name_column_index = column_index
			elif 'Last Name' in field:
				self.__last_name_column_index = column_index
		# Extract the data we care about, keyed by the full name of the respondent and then by the organization name
		respondent_name_from_row = lambda row: row[self.__last_name_column_index] + ', ' + row[self.__first_name_column_index]
		for row in self.raw_data[self.__data_start_row_index:]:
			respondent_name = respondent_name_from_row(row)
			self.respondents.append(respondent_name)
			self.data[respondent_name] = dict()
			for organization_name, column_index in self.__organizations_by_column_index.items():
				self.data[respondent_name][organization_name] = int(row[column_index] or self.__NONRESPONSE_VALUE_TEXT)

		self.respondents = sorted(self.respondents)
		self.organizations = sorted(self.organizations)
