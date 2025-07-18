import csv

input_csv = 'demographics.csv'
output_js = 'demographics_2025.js'

with open(input_csv, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    
    data = {}
    for row in reader:
        if row['Year'] == '2025':
            country = row['Country']
            data[country] = {
                "GDP_per_capita": float(row['GDP_per_capita']),
                "Life_expectancy": float(row['Life_expectancy']),
                "Urbanization": float(row['Urbanization']),
                "Fertility_rate": float(row['Fertility_rate']),
                "Death_rate": float(row['Death_rate']),
                "Migration_rate": float(row['Migration_rate'])
            }

# Write JS file with the object assigned to a variable
with open(output_js, 'w', encoding='utf-8') as jsfile:
    jsfile.write('const demographicData2025 = ')
    jsfile.write(str(data).replace("'", '"'))  # convert to double quotes for JSON-like format
    jsfile.write(';')
    
print(f"JavaScript data written to {output_js}")
