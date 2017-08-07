if (typeof jQuery === 'undefined') {
  throw new Error('Bootstrap\'s JavaScript requires jQuery')
}

+function($) {
    $(function () {
        $('#csv-file-input').on('change', function (e) {
            var csvFile = this.files[0];
            $('#file-input-form').slideUp(100);
            csvToTable.validateFile(csvFile);
        });
    });
}(jQuery);

// Forked from https://codepen.io/tjohnst1/pen/WwGwyp
var csvToTable = {
    // If the input file is a CSV, call the 'buildTable' function with its contents.
    validateFile: function (csvFile) {
        var that = this,
            file_type = csvFile.type,
            filename_parts = csvFile.name.split('.'),
            file_extension = filename_parts[filename_parts.length - 1].toLowerCase();
        if (file_type === 'text/csv' || file_extension === 'csv') {
            Papa.parse(csvFile, {
                complete: function (results) {
                    console.log(results.data);
                    qualtrics_results = results.data;
                    // Clean the data and reshape the table
                    pref_data = that.parseTable(qualtrics_results);
                    // Run the Munkres algorithm against it
                    assignments = that.computeAssignments(pref_data);
                    // Display the results
                    that.buildTable(assignments);
                }
            });
        } else {
            alert('This file type is not supported.');
            alert('The file type is ' + csvFile.type + ' and the filename is ' + csvFile.name);
        }
    },
    // Process the raw results from a Qualtrics CSV file to a matrix suitable for computation
    parseTable: function (qualtrics_results) {
        var header_row,
            studentid_column_index = -1,
            job_id_to_column_index = {},
            job_ids = new Array(),
            student_ids = new Array(),
            job_rankings = new Array();
        
        header_row = qualtrics_results[1];
        for ( var i = 0; i < header_row.length; i++ ) {
            if ( header_row[i] === "Name" ) {
                studentid_column_index = i;
            }
        }
        // If studentid_column_index is still -1, there's a problem with this file
        for ( var i = 0; i < header_row.length; i++ ) {
            if ( header_row[i].endsWith("-Rank") ) {
                var match = /-(.*?)\s*-Rank/g.exec(header_row[i]);
                var job_id = match[1];
                job_id_to_column_index[job_id] = i;
                job_ids.push(job_id);
            }
        }        
        console.log("job_ids");
        console.log(job_ids);
        console.log("job_id_to_column_index");
        console.log(job_id_to_column_index);
        
        
        for (var row = 2; row < qualtrics_results.length; row++ ) {
            var data_row = qualtrics_results[row],
                student_id = data_row[studentid_column_index],
                rankings_row = new Array();
            student_ids.push(student_id);
            for (var i = 0; i < job_ids.length; i++ ) {
                var job_id = job_ids[i],
                    job_id_column_index = job_id_to_column_index[job_id];
                rankings_row.push(data_row[job_id_column_index]);
            }
            job_rankings.push(rankings_row);
        }
        
        console.log("student_ids");
        console.log(student_ids);
        console.log("job_rankings");
        console.log(job_rankings);
        
        return job_rankings;
    },
    computeAssignments: function (data_table) {
        return data_table;  
    },
    // Construct a table from the CSV data.
    buildTable: function (dataArr) {
        var body = document.getElementsByTagName('body')[0],
            that = this,
            i;

        // If a table is already present on the page, remove it.
        this.clearTable();

        var table = document.createElement('table'),
            thead = document.createElement('thead'),
            tbody = document.createElement('tbody'),
            trow;

        table.className = "table table-striped panel panel-default";
        table.id = "csv-table";

        // Loop through the data, calling the 'buildTableRow' function to construct table rows and append the results to either the thead or trow depending on the content.
        for (i = 0; i < dataArr.length; i++) {
            if (i === 0) {
                trow = that.buildTableRow(dataArr[i], 'th');
                thead.appendChild(trow);
            } else {
                // Check that each row actually has content in it. 
                if (dataArr[i]) {
                    trow = that.buildTableRow(dataArr[i], 'td');
                    if (trow) {
                        tbody.appendChild(trow);
                    }
                }
            }
        }

        // Place the newly formed table on the page.
        table.appendChild(thead);
        table.appendChild(tbody);
        body.appendChild(table);

        // https://datatables.net/reference/option/
        jQuery('#csv-table').DataTable({
            //     "order": [[1, "asc"], [2, "asc"]],
            "paging": false
        });
    },
    // Constructs table rows from CSV strings.
    buildTableRow: function (dataArr, elementType) {
        var i;
        
        // Check that each data item isn't a blank string
        if (dataArr[0].trim().length !== 0) {
            var row = document.createElement('tr');
            // Construct either a td or th element from each item depending on the passed in element type.
            for (i = 0; i < dataArr.length; i++) {
                var element = document.createElement(elementType);
                element.innerHTML = dataArr[i];
                row.appendChild(element);
            }
            return row;
        }
    },
    // Checks if there is a table already displayed and deletes it if there is.
    clearTable: function() {
        var table = document.getElementById('csv-table');

        if (table) {
            var siteBody = document.getElementsByTagName('body')[0];
            siteBody.removeChild(table);
        }
    }
}

