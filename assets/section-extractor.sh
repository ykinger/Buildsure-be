#!/bin/bash

# Script to extract sections from the building code document into JSON format
# Usage: ./extract_sections.sh input_file.md output_file.json

if [ $# -ne 2 ]; then
    echo "Usage: $0 <input_file> <output_file>"
    echo "Example: $0 bare.md sections.json"
    exit 1
fi

input_file="$1"
output_file="$2"

# Check if input file exists
if [ ! -f "$input_file" ]; then
    echo "Error: Input file '$input_file' not found!"
    exit 1
fi

# Temporary file for processing
temp_file=$(mktemp)

# Process the input file
awk '
BEGIN {
    print "["
    section_count = 0
    body = ""
    in_section = 0
}

# Match lines that start with a section number (e.g., "3.00", "3.01", etc.)
/^[0-9]+\.[0-9]+ / {
    # If this is not the first section, close the previous one
    if (section_count > 0) {
        # Clean and escape the body text
        gsub(/^[ \t\n]+/, "", body)  # Remove leading whitespace
        gsub(/[ \t\n]+$/, "", body)  # Remove trailing whitespace
        gsub(/\\/, "\\\\", body)     # Escape backslashes
        gsub(/"/, "\\\"", body)      # Escape quotes
        gsub(/\n/, "\\n", body)      # Convert newlines to escaped newlines
        gsub(/\r/, "", body)         # Remove carriage returns
        
        printf "%s\"\n    },\n", body
    }
    
    # Extract section number and title
    section_line = $0
    space_pos = index(section_line, " ")
    section_num = substr(section_line, 1, space_pos - 1)
    section_title = substr(section_line, space_pos + 1)
    
    # Clean up title
    gsub(/^[ \t]+/, "", section_title)
    gsub(/[ \t]+$/, "", section_title)
    gsub(/"/, "\\\"", section_title)
    
    # Start new section
    printf "    {\n"
    printf "        \"question_number\": \"%s\",\n", section_num
    printf "        \"question_title\": \"%s\",\n", section_title
    printf "        \"question_guide\": \""
    
    body = ""
    section_count++
    in_section = 1
    next
}

# For all other lines, add to the current section body if we are in a section
{
    if (in_section && section_count > 0) {
        # Skip completely empty lines, but preserve content
        if (length($0) > 0 || (length($0) == 0 && length(body) > 0 && body !~ /\n$/)) {
            if (body != "" && length($0) > 0) {
                body = body "\n"
            }
            body = body $0
        }
    }
}

END {
    # Close the last section if any sections were found
    if (section_count > 0) {
        # Clean and escape the body text
        gsub(/^[ \t\n]+/, "", body)  # Remove leading whitespace
        gsub(/[ \t\n]+$/, "", body)  # Remove trailing whitespace
        gsub(/\\/, "\\\\", body)     # Escape backslashes
        gsub(/"/, "\\\"", body)      # Escape quotes  
        gsub(/\n/, "\\n", body)      # Convert newlines to escaped newlines
        gsub(/\r/, "", body)         # Remove carriage returns
        
        printf "%s\"\n    }\n", body
    }
    print "]"
}' "$input_file" > "$temp_file"

# Validate JSON and write to output file
if command -v jq >/dev/null 2>&1; then
    # If jq is available, use it to validate and pretty-print the JSON
    if jq . "$temp_file" > "$output_file" 2>/dev/null; then
        echo "Successfully created JSON file: $output_file"
        echo "Number of sections extracted: $(jq length "$output_file")"
    else
        echo "Error: Generated JSON is invalid. Check the temp file: $temp_file"
        exit 1
    fi
else
    # If jq is not available, just copy the file and warn
    cp "$temp_file" "$output_file"
    echo "Successfully created JSON file: $output_file"
    echo "Note: Install 'jq' for JSON validation and pretty-printing"
fi

# Clean up
rm "$temp_file"

echo "Extraction complete!"
