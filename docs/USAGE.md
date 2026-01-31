# Tableau Metadata Extractor - Usage Guide

## Table of Contents
1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [CLI Commands](#cli-commands)
4. [Python API](#python-api)
5. [Output Formats](#output-formats)
6. [Examples](#examples)
7. [Troubleshooting](#troubleshooting)

---

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Install Dependencies

```bash
cd /Users/dhrsharm/tableau_metadata_extractor
pip install -r requirements.txt
```

### Verify Installation

```bash
python main.py --help
```

---

## Quick Start

### Extract Metadata from a Workbook

```bash
# Basic extraction (outputs to console)
python main.py extract /path/to/workbook.twbx

# Save to JSON file
python main.py extract /path/to/workbook.twbx -o metadata.json

# Save to Excel
python main.py extract /path/to/workbook.twbx -f excel -o metadata.xlsx

# Save to HTML report
python main.py extract /path/to/workbook.twbx -f html -o report.html
```

---

## CLI Commands

### 1. `extract` - Extract Metadata

Extract comprehensive metadata from a local Tableau workbook.

```bash
python main.py extract <FILE_PATH> [OPTIONS]
```

**Arguments:**
- `FILE_PATH` - Path to .twbx or .twb file

**Options:**
| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--output` | `-o` | Output file path | stdout |
| `--format` | `-f` | Output format (json/excel/html/summary) | json |
| `--validate/--no-validate` | | Run validation after extraction | --validate |
| `--verbose` | `-v` | Show detailed output | False |

**Examples:**

```bash
# Extract to JSON
python main.py extract sales_dashboard.twbx -o sales_metadata.json

# Extract to Excel with validation disabled
python main.py extract sales_dashboard.twbx -f excel -o metadata.xlsx --no-validate

# Verbose extraction with HTML output
python main.py extract sales_dashboard.twbx -f html -o report.html -v
```

---

### 2. `validate` - Validate Metadata

Check extracted metadata for completeness and accuracy.

```bash
python main.py validate <FILE_PATH> [OPTIONS]
```

**Options:**
| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--strict` | | Treat warnings as errors | False |
| `--output` | `-o` | Save validation report | None |

**Examples:**

```bash
# Basic validation
python main.py validate workbook.twbx

# Strict validation with report
python main.py validate workbook.twbx --strict -o validation_report.txt
```

**Validation Checks:**
- ✅ Workbook structure integrity
- ✅ Data source field existence
- ✅ Calculated field formula validity
- ✅ Filter configuration completeness
- ✅ Dashboard worksheet references
- ✅ Action source/target validity
- ✅ Relationship consistency

---

### 3. `compare` - Compare Extraction Methods

Compare metadata from local XML parsing (Option A) vs Tableau Server API (Option C).

```bash
python main.py compare <FILE_PATH> --server <URL> [OPTIONS]
```

**Required:**
- `FILE_PATH` - Path to local .twbx file
- `--server` / `-s` - Tableau Server URL

**Authentication (one required):**
| Option | Description |
|--------|-------------|
| `--token-name` | Personal access token name |
| `--token-secret` | Personal access token secret |
| `--username` / `-u` | Username |
| `--password` / `-p` | Password |

**Optional:**
| Option | Description |
|--------|-------------|
| `--site` | Site content URL (empty for default) |
| `--workbook-name` / `-w` | Workbook name on server |
| `--project` | Project name filter |
| `--output` / `-o` | Save comparison report |

**Examples:**

```bash
# Compare using personal access token
python main.py compare workbook.twbx \
  -s https://tableau.company.com \
  --token-name MyToken \
  --token-secret abc123xyz

# Compare with specific workbook name
python main.py compare local_workbook.twbx \
  -s https://tableau.company.com \
  -u admin -p password123 \
  -w "Published Workbook Name" \
  -o comparison_report.txt
```

---

### 4. `list-workbooks` - List Server Workbooks

List all accessible workbooks on Tableau Server.

```bash
python main.py list-workbooks --server <URL> [OPTIONS]
```

**Examples:**

```bash
# List all workbooks
python main.py list-workbooks \
  -s https://tableau.company.com \
  --token-name MyToken \
  --token-secret abc123

# Filter by project
python main.py list-workbooks \
  -s https://tableau.company.com \
  --token-name MyToken \
  --token-secret abc123 \
  --project "Sales Analytics"
```

---

## Python API

### Basic Extraction

```python
from extractors.xml_extractor import XMLMetadataExtractor

# Initialize extractor
extractor = XMLMetadataExtractor("/path/to/workbook.twbx")

# Extract metadata
metadata = extractor.extract()

# Access workbook info
print(f"Workbook: {metadata.name}")
print(f"Version: {metadata.version}")
print(f"Sheets: {metadata.total_sheets}")
print(f"Calculated Fields: {metadata.total_calculated_fields}")
```

### Accessing Data Sources

```python
for ds in metadata.datasources:
    print(f"\nData Source: {ds.display_name}")
    print(f"  Connection: {ds.connection_type}")
    print(f"  Fields: {len(ds.fields)}")
    print(f"  Calculated Fields: {len(ds.calculated_fields)}")
    
    # List fields
    for field in ds.fields:
        print(f"    - {field.name} ({field.data_type.value}, {field.role.value})")
    
    # List calculated fields with formulas
    for calc in ds.calculated_fields:
        print(f"    - {calc.name}: {calc.formula}")
        print(f"      Type: {calc.calculation_type.value}")
        print(f"      Aggregations: {calc.aggregations_used}")
```

### Accessing Worksheets and Visuals

```python
for sheet in metadata.sheets:
    print(f"\nSheet: {sheet.name}")
    
    if sheet.visual:
        print(f"  Chart Type: {sheet.visual.chart_type.value}")
        print(f"  Inferred: {sheet.visual.chart_type_inferred}")
        
        # Rows and columns
        print(f"  Rows: {[r['field'] for r in sheet.visual.rows]}")
        print(f"  Columns: {[c['field'] for c in sheet.visual.columns]}")
        
        # Encodings
        if sheet.visual.color:
            print(f"  Color: {sheet.visual.color['field']}")
        if sheet.visual.size:
            print(f"  Size: {sheet.visual.size['field']}")
```

### Accessing Filters with Explanations

```python
for sheet in metadata.sheets:
    print(f"\nFilters in '{sheet.name}':")
    
    for f in sheet.filters:
        print(f"  Field: {f.field}")
        print(f"  Type: {f.filter_type.value}")
        print(f"  Explanation: {f.calculation_explanation}")
        
        # Detailed filter info
        if f.filter_type.value == "categorical":
            print(f"    Include: {f.include_values}")
            print(f"    Exclude: {f.exclude_values}")
        elif f.filter_type.value == "range":
            print(f"    Min: {f.range_min}, Max: {f.range_max}")
        elif f.filter_type.value == "relative_date":
            print(f"    {f.relative_date_type} {f.relative_date_value} {f.relative_date_period}")
        elif f.filter_type.value == "top_n":
            print(f"    {f.top_n_direction} {f.top_n_value} by {f.top_n_field}")
```

### Accessing Dashboards

```python
for dash in metadata.dashboards:
    print(f"\nDashboard: {dash.name}")
    print(f"  Size: {dash.width}x{dash.height}")
    print(f"  Worksheets: {dash.worksheets}")
    
    # Zones
    print(f"  Zones ({len(dash.zones)}):")
    for zone in dash.zones:
        print(f"    - {zone.zone_type}: {zone.name or zone.worksheet_name}")
        print(f"      Position: ({zone.x}, {zone.y})")
        print(f"      Size: {zone.width}x{zone.height}")
    
    # Actions
    print(f"  Actions ({len(dash.actions)}):")
    for action in dash.actions:
        print(f"    - {action.name} ({action.action_type})")
        print(f"      Source: {action.source_worksheets}")
        print(f"      Target: {action.target_worksheets}")
```

### Accessing Relationships

```python
print("\nRelationships:")
for rel in metadata.relationships:
    print(f"  [{rel.relationship_type}]")
    print(f"    {rel.source_type}: {rel.source_name}")
    print(f"    → {rel.target_type}: {rel.target_name}")
    if rel.description:
        print(f"    Description: {rel.description}")
```

### Generating Output

```python
from utils.output import OutputGenerator

output = OutputGenerator(metadata)

# JSON
json_str = output.to_json()  # Returns string
output.to_json("/path/to/metadata.json")  # Saves to file

# Excel
output.to_excel("/path/to/metadata.xlsx")

# HTML
output.to_html("/path/to/report.html")

# Console summary
print(output.to_summary())
```

### Validation

```python
from utils.validation import MetadataValidator

validator = MetadataValidator()
result = validator.validate(metadata)

print(f"Valid: {result.is_valid}")
print(f"Score: {result.get_score()}/100")
print(f"Errors: {result.errors_count}")
print(f"Warnings: {result.warnings_count}")

for issue in result.issues:
    print(f"[{issue.level.value}] {issue.category}: {issue.message}")
```

### Comparison (Option A vs Option C)

```python
from extractors.xml_extractor import XMLMetadataExtractor
from extractors.metadata_api import TableauMetadataAPIClient
from utils.comparison import MetadataComparator

# Extract from local file (Option A)
xml_extractor = XMLMetadataExtractor("workbook.twbx")
xml_metadata = xml_extractor.extract()

# Extract from server (Option C)
api_client = TableauMetadataAPIClient(
    server_url="https://tableau.company.com",
    token_name="MyToken",
    token_secret="secret123"
)
api_client.authenticate()
api_metadata = api_client.get_workbook_metadata("Workbook Name")
api_client.close()

# Compare
comparator = MetadataComparator()
result = comparator.compare(xml_metadata, api_metadata)

print(f"Match: {result.get_match_percentage()}%")
print(f"Differences: {result.total_differences}")
print(comparator.generate_report(result))
```

---

## Output Formats

### JSON Output Structure

```json
{
  "name": "Sales Dashboard",
  "version": "2023.1",
  "extraction_timestamp": "2026-01-31T12:00:00",
  "datasources": [
    {
      "name": "Sales Data",
      "connection_type": "SQL Server",
      "fields": [...],
      "calculated_fields": [...]
    }
  ],
  "sheets": [
    {
      "name": "Revenue by Region",
      "visual": {
        "chart_type": "bar",
        "rows": [...],
        "columns": [...]
      },
      "filters": [
        {
          "field": "Region",
          "filter_type": "categorical",
          "calculation_explanation": "Show only records where [Region] is one of: 'West', 'East'"
        }
      ]
    }
  ],
  "dashboards": [...],
  "parameters": [...],
  "relationships": [...]
}
```

### Excel Output Sheets

| Sheet | Contents |
|-------|----------|
| Summary | Workbook overview and statistics |
| Fields | All fields with data types and roles |
| Calculated Fields | Formulas, types, complexity scores |
| Worksheets | Chart types, dimensions, measures |
| Filters | Filter logic with explanations |
| Dashboards | Zones, actions, worksheets |
| Parameters | Values, ranges, constraints |
| Relationships | All linkages between components |

### HTML Report Sections

- 📊 Summary Statistics (cards with counts)
- 📋 Worksheets (table with chart types)
- 🔢 Calculated Fields (formulas with complexity)
- 🔍 Filters (with explanations)
- 🔗 Relationships (source → target)

---

## Examples

### Example 1: Migration Documentation

```python
from extractors.xml_extractor import XMLMetadataExtractor
from utils.output import OutputGenerator

# Extract all metadata
extractor = XMLMetadataExtractor("sales_dashboard.twbx")
metadata = extractor.extract()

# Generate comprehensive Excel documentation
output = OutputGenerator(metadata)
output.to_excel("migration_documentation.xlsx")

print("Documentation generated!")
print(f"Total calculated fields to migrate: {metadata.total_calculated_fields}")
```

### Example 2: Find All LOD Calculations

```python
extractor = XMLMetadataExtractor("complex_workbook.twbx")
metadata = extractor.extract()

print("LOD Expressions Found:")
for ds in metadata.datasources:
    for calc in ds.calculated_fields:
        if calc.is_lod:
            print(f"\n  {calc.name}")
            print(f"    LOD Type: {calc.lod_type}")
            print(f"    Dimensions: {calc.lod_dimensions}")
            print(f"    Formula: {calc.formula}")
```

### Example 3: Dashboard Impact Analysis

```python
extractor = XMLMetadataExtractor("enterprise_dashboard.twbx")
metadata = extractor.extract()

# Find all fields used in a specific dashboard
dashboard_name = "Executive Summary"

for dash in metadata.dashboards:
    if dash.name == dashboard_name:
        print(f"Dashboard: {dash.name}")
        print(f"Worksheets: {dash.worksheets}")
        
        # Get all fields from worksheets in this dashboard
        all_fields = set()
        for ws_name in dash.worksheets:
            for sheet in metadata.sheets:
                if sheet.name == ws_name:
                    all_fields.update(sheet.all_fields_used)
        
        print(f"Fields impacted: {all_fields}")
```

### Example 4: Filter Audit

```python
extractor = XMLMetadataExtractor("workbook.twbx")
metadata = extractor.extract()

print("Filter Audit Report")
print("=" * 60)

for sheet in metadata.sheets:
    if sheet.filters:
        print(f"\n{sheet.name}:")
        for f in sheet.filters:
            status = "⚠️ CONTEXT" if f.is_context_filter else "  "
            print(f"  {status} {f.field}: {f.calculation_explanation}")
```

---

## Troubleshooting

### Error: "File is not a zip file"

**Cause:** The .twbx file is not a valid ZIP archive (might be HTML from Tableau Public)

**Solution:** 
```bash
file your_workbook.twbx
```
If it shows "HTML document", you need to download the actual .twbx from Tableau Desktop.

### Error: "No .twb file found"

**Cause:** The TWBX archive doesn't contain a TWB file

**Solution:** Verify the workbook was saved correctly from Tableau Desktop.

### Error: "Authentication failed"

**Cause:** Invalid credentials for Tableau Server

**Solution:** 
1. Verify your Personal Access Token is still valid
2. Check the site content URL is correct
3. Ensure your account has Metadata API access

### Performance: Large Workbooks

For workbooks with many sheets/fields:
```python
# Extract with progress tracking
import time
start = time.time()
metadata = extractor.extract()
print(f"Extraction took {time.time() - start:.2f}s")
```

### Missing Fields in Output

**Cause:** Fields might be hidden in Tableau

**Solution:** Check the `is_hidden` property:
```python
hidden_fields = [f for f in ds.fields if f.is_hidden]
print(f"Hidden fields: {len(hidden_fields)}")
```
