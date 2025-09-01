#!/bin/bash

# Output file for the summary
OUTPUT="repo_summary.txt"

# Write header with timestamp to output file (overwrite if exists)
echo "�� Codebase Summary ($(date))" > "$OUTPUT"
echo "===================================" >> "$OUTPUT"

# Find files with specified extensions, excluding certain directories,
# and process each file to add a preview of its content to the summary
find . -type f \( \
    -name "*.py" -o -name "*.go" -o -name "*.js" -o -name "*.ts" -o \
    -name "*.yaml" -o -name "*.sh" -o -name "*.html" -o -name "*.md" \
\) \
! -path "*/node_modules/*" \
! -path "*/.git/*" \
! -path "*/__pycache__/*" \
! -path "./sh/*" | while read -r file; do
    echo -e "\n\n🔹 FILE: $file" >> "$OUTPUT"
    echo "-----------------------------------" >> "$OUTPUT"
    cat "$file" >> "$OUTPUT"
done

echo -e "\n\n✅ Done. Summary saved to $OUTPUT"

