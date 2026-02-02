# Tableau Metadata Extractor

A comprehensive tool to extract **100% accurate metadata** from Tableau workbooks (.twbx/.twb files), including KPIs, calculated fields, visuals, filters, and their relationships.

## Features

- **Complete Field Extraction** - All fields with data types, roles, and aggregations
- **Calculated Field Analysis** - Formulas, LOD expressions, table calculations with complexity scoring
- **Visual Detection** - Chart types (bar, line, pie, etc.) with axis configurations
- **Filter Logic Parsing** - All filter types with **human-readable explanations**
- **Dashboard Metadata** - Zones, pixel positions, actions, and interactivity
- **Relationship Mapping** - Field→Sheet, Calc→Field, Sheet→Dashboard linkages
- **Metric Detail Rows** - Flattened view of each metric per worksheet with full context (NEW!)
- **Dual Extraction Methods** - Option A (XML) for local files, Option C (API) for server
- **Multiple Output Formats** - JSON, Excel (with Metrics sheet), HTML, Console

## Quick Start

```bash
# Install dependencies
cd tableau_metadata_extractor
pip install -r requirements.txt

# Extract metadata to JSON (default format)
python main.py extract /path/to/workbook.twbx -o metadata.json

# Extract to Excel (9 sheets: Summary, Fields, Calculated Fields, Worksheets, Filters, Dashboards, Parameters, Relationships, Metrics)
python main.py extract /path/to/workbook.twbx -f excel -o metadata.xlsx

# Extract to interactive HTML report
python main.py extract /path/to/workbook.twbx -f html -o report.html

# Extract summary to text file
python main.py extract /path/to/workbook.twbx -f summary -o summary.txt

# Validate metadata completeness
python main.py validate /path/to/workbook.twbx
```

---

## Usage Commands

### Option A: XML Extraction (Local Files)

Extract metadata from local `.twbx` or `.twb` files with 100% accuracy.

```bash
# Basic extraction to JSON
python main.py extract /path/to/workbook.twbx -o metadata.json

# Extract to Excel (multi-sheet workbook)
python main.py extract /path/to/workbook.twbx -f excel -o metadata.xlsx

# Extract to HTML report
python main.py extract /path/to/workbook.twbx -f html -o report.html

# Extract with verbose output
python main.py extract /path/to/workbook.twbx -o metadata.json -v

# Extract without validation
python main.py extract /path/to/workbook.twbx -o metadata.json --no-validate
```

**Options:**
| Option | Short | Description |
|--------|-------|-------------|
| `--output` | `-o` | Output file path |
| `--format` | `-f` | Output format: `json`, `excel`, `html`, `summary` |
| `--validate` | | Run validation (default: enabled) |
| `--verbose` | `-v` | Show detailed output |

---

### Option C: Metadata API (Tableau Server)

Extract metadata from published workbooks on Tableau Server/Online and compare with local extraction.

```bash
# Compare using Personal Access Token (recommended)
python main.py compare /path/to/workbook.twbx \
  --server https://tableau.yourcompany.com \
  --token-name "YourTokenName" \
  --token-secret "YourTokenSecret"

# Compare using username/password
python main.py compare /path/to/workbook.twbx \
  --server https://tableau.yourcompany.com \
  --username admin \
  --password yourpassword

# With specific site and workbook name
python main.py compare /path/to/workbook.twbx \
  --server https://tableau.yourcompany.com \
  --site "your-site-name" \
  --workbook-name "Published Workbook Name" \
  --token-name "YourTokenName" \
  --token-secret "YourTokenSecret" \
  --output comparison_report.txt

# List all workbooks on server
python main.py list-workbooks \
  --server https://tableau.yourcompany.com \
  --token-name "YourTokenName" \
  --token-secret "YourTokenSecret"

# Filter workbooks by project
python main.py list-workbooks \
  --server https://tableau.yourcompany.com \
  --token-name "YourTokenName" \
  --token-secret "YourTokenSecret" \
  --project "Sales Analytics"
```

**Authentication Options:**
| Option | Description |
|--------|-------------|
| `--token-name` | Personal Access Token name (recommended) |
| `--token-secret` | Personal Access Token secret |
| `--username` / `-u` | Username (alternative to PAT) |
| `--password` / `-p` | Password (alternative to PAT) |

**Other Options:**
| Option | Description |
|--------|-------------|
| `--server` / `-s` | Tableau Server URL (required) |
| `--site` | Site content URL (empty for default site) |
| `--workbook-name` / `-w` | Workbook name on server (defaults to file name) |
| `--project` | Filter by project name |
| `--output` / `-o` | Save comparison report to file |

---

### Validation Command

Validate extracted metadata for completeness and accuracy.

```bash
# Basic validation
python main.py validate /path/to/workbook.twbx

# Strict validation (treat warnings as errors)
python main.py validate /path/to/workbook.twbx --strict

# Save validation report
python main.py validate /path/to/workbook.twbx -o validation_report.txt
```

---

### Command Summary

| Command | Method | Description |
|---------|--------|-------------|
| `extract` | Option A | Extract from local .twbx/.twb file |
| `compare` | Option A + C | Compare local vs Tableau Server API |
| `validate` | Option A | Validate metadata completeness |
| `list-workbooks` | Option C | List workbooks on Tableau Server |

---

## Documentation

| Document | Description |
|----------|-------------|
| [PLAN.md](docs/PLAN.md) | Technical architecture and implementation plan |
| [USAGE.md](docs/USAGE.md) | Detailed usage guide with CLI and Python API examples |
| [EXPLANATION.md](docs/EXPLANATION.md) | How the extraction works, data models, filter parsing |

## What Gets Extracted

### Data Sources
- Connection type, server, database
- Tables and joins
- Custom SQL

### Fields (KPIs)
- Name, caption, data type
- Role (dimension/measure)
- Default aggregation
- Hidden status

### Calculated Fields
- Full formula
- Calculation type (simple, aggregate, LOD, table calc)
- Functions and aggregations used
- Referenced fields
- Complexity score

### Worksheets
- Chart type (bar, line, area, pie, etc.)
- Rows/columns encodings
- Color, size, shape, label, detail, tooltip
- Axis configuration
- Reference lines, trend lines

### Filters (with Calculation Explanations)
```
"Show only records where [Region] is one of: 'West', 'East'"
"Show records where [Sales] is between 1000 and 5000"
"Show records from the last 30 days"
"Show top 10 values of [Product] by SUM(Sales)"
```

### Dashboards
- Size (width x height)
- Zones with pixel positions
- Worksheet references
- Actions (filter, highlight, URL)
- Exposed filters and parameters

### Relationships
- Field → Sheet usage
- Calculated field → Field dependencies
- Sheet → Dashboard membership
- Action linkages
- Parameter usage

### Metrics (Flattened View) - NEW!
One row per metric-worksheet combination with full context:
- Metric name, type, and calculation
- Formula and referenced fields
- Worksheet and shelf position (rows, columns, color, size, label, etc.)
- All filters applied with explanations
- Dashboard context
- Complexity score

## Output Formats

### JSON (`-f json` - default)
Complete metadata in JSON format, ideal for programmatic access and integration.

```bash
python main.py extract workbook.twbx -f json -o metadata.json
```

### Excel (`-f excel`)
Multi-sheet Excel workbook with 9 sheets for easy analysis:

| Sheet | Description |
|-------|-------------|
| **Summary** | Workbook info, version, extraction timestamp, statistics |
| **Fields** | All fields with data types, roles, aggregations |
| **Calculated Fields** | Formulas, calculation types, complexity scores |
| **Worksheets** | Chart types, dimensions, measures, filter counts |
| **Filters** | Filter types, values, conditions, explanations |
| **Dashboards** | Size, zones, actions, exposed filters |
| **Parameters** | Types, current values, allowable values |
| **Relationships** | Field→Sheet, Calc→Field, Sheet→Dashboard mappings |
| **Metrics** | **One row per metric-worksheet combination** (see below) |

```bash
python main.py extract workbook.twbx -f excel -o metadata.xlsx
```

#### Metrics Sheet Columns
The Metrics sheet provides a denormalized view with one unique row per metric usage:

| Column | Description |
|--------|-------------|
| Metric Name | Field or calculated field name |
| Metric Caption | Display name |
| Metric Type | `calculated_field`, `measure`, `dimension`, or `unknown` |
| Data Source | Source data connection |
| Worksheet | Sheet where metric is used |
| Chart Type | Visualization type (bar, line, etc.) |
| Shelf Position | `rows`, `columns`, `color`, `size`, `label`, `detail`, `tooltip` |
| Formula | Full calculation formula |
| Formula (Readable) | Cleaned formula without internal prefixes |
| Calculation Type | `simple`, `aggregate`, `lod_fixed`, `table_calc`, etc. |
| Data Type | `string`, `integer`, `real`, `date`, etc. |
| Aggregation Used | How the metric is aggregated in this context |
| Aggregations in Formula | SUM, AVG, COUNT, etc. used in formula |
| Functions Used | All functions used (IF, CASE, etc.) |
| Referenced Fields | Fields this calculation depends on |
| Referenced Parameters | Parameters used in calculation |
| LOD Type | `FIXED`, `INCLUDE`, `EXCLUDE` if LOD expression |
| LOD Dimensions | Dimensions in LOD expression |
| LOD Expression | The LOD calculation expression |
| Filters Applied | List of filters on the worksheet |
| Filter Details | Summary of filter logic |
| Dashboards | Dashboards containing this worksheet |
| Complexity Score | 0-100 score for calculation complexity |

### HTML (`-f html`)
Interactive HTML report with collapsible sections and styled tables.

```bash
python main.py extract workbook.twbx -f html -o report.html
```

### Summary (`-f summary`)
Plain text summary for console output or quick review.

```bash
python main.py extract workbook.twbx -f summary -o summary.txt
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Extraction Methods                        │
├─────────────────────────────────────────────────────────────┤
│  ┌────────────────────┐     ┌────────────────────┐         │
│  │    Option A        │     │    Option C        │         │
│  │   XML Parser       │     │  Metadata API      │         │
│  │ (Local .twbx)      │     │ (Tableau Server)   │         │
│  │                    │     │                    │         │
│  │ ✓ 100% Accuracy    │     │ ✓ Server Access    │         │
│  │ ✓ Full Formulas    │     │ ✓ Bulk Processing  │         │
│  │ ✓ Pixel Positions  │     │ ✓ Usage Stats      │         │
│  └─────────┬──────────┘     └─────────┬──────────┘         │
│            │                          │                     │
│            └──────────┬───────────────┘                     │
│                       ▼                                     │
│            ┌────────────────────┐                          │
│            │ WorkbookMetadata   │                          │
│            │ (Unified Model)    │                          │
│            └─────────┬──────────┘                          │
│                      │                                      │
│       ┌──────────────┼──────────────┐                      │
│       ▼              ▼              ▼                      │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐                  │
│  │  JSON   │   │  Excel  │   │  HTML   │                  │
│  └─────────┘   └─────────┘   └─────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `extract` | Extract metadata from local .twbx/.twb file |
| `validate` | Validate extracted metadata for completeness |
| `compare` | Compare local extraction vs server API |
| `list-workbooks` | List workbooks on Tableau Server |

## Python API

### Option A: Local XML Extraction

```python
from extractors.xml_extractor import XMLMetadataExtractor
from utils.output import OutputGenerator

# Extract metadata from local file
extractor = XMLMetadataExtractor("workbook.twbx")
metadata = extractor.extract()

# Access data
print(f"Sheets: {metadata.total_sheets}")
print(f"Calculated Fields: {metadata.total_calculated_fields}")
print(f"Metric Rows: {len(metadata.metric_rows)}")

for sheet in metadata.sheets:
    print(f"Sheet: {sheet.name}")
    if sheet.visual:
        print(f"  Chart: {sheet.visual.chart_type.value}")
    for f in sheet.filters:
        print(f"  Filter: {f.calculation_explanation}")

# Access flattened metric rows (one row per metric-worksheet)
for metric in metadata.metric_rows[:5]:  # First 5 metrics
    print(f"Metric: {metric.metric_name}")
    print(f"  Type: {metric.metric_type}")
    print(f"  Worksheet: {metric.worksheet_name}")
    print(f"  Shelf: {metric.shelf_position}")
    print(f"  Formula: {metric.formula[:50] if metric.formula else 'N/A'}...")
    print(f"  Filters: {', '.join(metric.filters_applied)}")

# Export to various formats
output = OutputGenerator(metadata)
output.to_json("metadata.json")      # Full JSON with metric_rows
output.to_excel("metadata.xlsx")     # Excel with Metrics sheet
output.to_html("report.html")        # Interactive HTML report
```

### Option C: Tableau Server API

```python
from extractors.metadata_api import TableauMetadataAPIClient

# Connect to Tableau Server
client = TableauMetadataAPIClient(
    server_url="https://tableau.yourcompany.com",
    site_id="your-site",  # Empty string for default site
    token_name="YourTokenName",
    token_secret="YourTokenSecret"
)

# Authenticate
client.authenticate()

# List available workbooks
workbooks = client.list_workbooks(project_name="Sales Analytics")
for wb in workbooks:
    print(f"Workbook: {wb['name']} in {wb['projectName']}")

# Get metadata for a specific workbook
metadata = client.get_workbook_metadata("Workbook Name")
print(f"Sheets: {metadata.total_sheets}")

# Close connection
client.close()
```

### Compare Both Methods

```python
from extractors.xml_extractor import XMLMetadataExtractor
from extractors.metadata_api import TableauMetadataAPIClient
from utils.comparison import MetadataComparator

# Option A: Extract from local file
xml_extractor = XMLMetadataExtractor("workbook.twbx")
xml_metadata = xml_extractor.extract()

# Option C: Extract from server
api_client = TableauMetadataAPIClient(
    server_url="https://tableau.yourcompany.com",
    token_name="YourTokenName",
    token_secret="YourTokenSecret"
)
api_client.authenticate()
api_metadata = api_client.get_workbook_metadata("Workbook Name")
api_client.close()

# Compare results
comparator = MetadataComparator()
result = comparator.compare(xml_metadata, api_metadata)

print(f"Match Percentage: {result.get_match_percentage()}%")
print(f"Differences Found: {result.total_differences}")
print(comparator.generate_report(result))
```

## Output Example

### JSON Structure
```json
{
  "name": "Sales Dashboard",
  "version": "2023.1",
  "datasources": [{
    "name": "Sales Data",
    "fields": [{
      "name": "Sales",
      "data_type": "real",
      "role": "measure"
    }],
    "calculated_fields": [{
      "name": "Profit Ratio",
      "formula": "SUM([Profit]) / SUM([Sales])",
      "calculation_type": "aggregate",
      "aggregations_used": ["SUM"],
      "referenced_fields": ["Profit", "Sales"]
    }]
  }],
  "sheets": [{
    "name": "Revenue by Region",
    "visual": {
      "chart_type": "bar",
      "rows": [{"field": "Region"}],
      "columns": [{"field": "Sales", "aggregation": "sum"}]
    },
    "filters": [{
      "field": "Region",
      "filter_type": "categorical",
      "calculation_explanation": "Show records where [Region] equals 'West'"
    }]
  }],
  "relationships": [...],
  "metric_rows": [{
    "metric_name": "Profit Ratio",
    "metric_type": "calculated_field",
    "worksheet_name": "Revenue by Region",
    "shelf_position": "columns",
    "formula": "SUM([Profit]) / SUM([Sales])",
    "calculation_type": "aggregate",
    "filters_applied": ["Region"],
    "filter_details": [{
      "field": "Region",
      "type": "categorical",
      "explanation": "Show records where [Region] equals 'West'"
    }],
    "dashboards_containing_worksheet": ["Executive Dashboard"],
    "complexity_score": 5
  }]
}
```

## Project Structure

```
tableau_metadata_extractor/
├── main.py                 # CLI entry point
├── requirements.txt        # Dependencies
├── README.md              # This file
├── docs/
│   ├── PLAN.md            # Technical architecture
│   ├── USAGE.md           # Detailed usage guide
│   └── EXPLANATION.md     # How it works
├── samples/               # Place .twbx files here
├── extractors/
│   ├── xml_extractor.py   # Option A: XML parsing
│   └── metadata_api.py    # Option C: Server API
├── models/
│   └── metadata_models.py # Pydantic data models
└── utils/
    ├── comparison.py      # Compare extraction methods
    ├── validation.py      # Metadata validation
    └── output.py          # JSON/Excel/HTML output
```

## Requirements

- Python 3.8+
- lxml
- pydantic
- click
- rich
- requests (for Option C)
- openpyxl (for Excel output)

## Comparison: Option A vs Option C

| Feature | Option A (XML) | Option C (API) |
|---------|----------------|----------------|
| Source | Local .twbx/.twb | Tableau Server/Online |
| Accuracy | 100% | ~95% |
| Offline | ✅ | ❌ |
| Full Formulas | ✅ | ⚠️ Partial |
| Filter Details | ✅ | ⚠️ Limited |
| Pixel Positions | ✅ | ❌ |
| Usage Stats | ❌ | ✅ |
| Bulk Processing | Manual | ✅ |

## License

MIT License
