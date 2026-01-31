# Tableau Metadata Extractor

A comprehensive tool to extract 100% accurate metadata from Tableau workbooks (.twbx/.twb files) and optionally compare with Tableau Server Metadata API.

## Features

### Option A: Local XML Parser (Primary)
- Extract all KPIs, fields, and their data types
- Parse calculated fields with formulas and dependencies
- Identify visual types (bar, line, pie, etc.) with axis configurations
- Extract filters and their calculation logic
- Map relationships between fields, worksheets, and dashboards
- Support for LOD expressions and table calculations

### Option C: Tableau Metadata API (Comparison)
- Query published workbooks on Tableau Server/Online
- GraphQL-based metadata extraction
- Compare local parsing with server metadata

## Installation

```bash
cd tableau_metadata_extractor
pip install -r requirements.txt
```

## Usage

### Extract Metadata from Local File

```bash
python main.py extract /path/to/workbook.twbx --output metadata.json
```

### Compare Local vs Server Metadata

```bash
python main.py compare /path/to/workbook.twbx \
  --server https://tableau.yourcompany.com \
  --site your-site \
  --project "Your Project" \
  --workbook "Workbook Name"
```

### Python API

```python
from extractors.xml_extractor import XMLMetadataExtractor
from extractors.metadata_api import TableauMetadataAPIClient

# Option A: Local file extraction
extractor = XMLMetadataExtractor("path/to/workbook.twbx")
metadata = extractor.extract()
print(metadata.to_json())

# Option C: Metadata API
client = TableauMetadataAPIClient(
    server_url="https://tableau.yourcompany.com",
    token_name="your-token-name",
    token_secret="your-token-secret"
)
api_metadata = client.get_workbook_metadata("workbook-name")
```

## Output Structure

```json
{
  "workbook": {
    "name": "Sales Dashboard",
    "version": "2023.1"
  },
  "sheets": [...],
  "fields": [...],
  "calculated_fields": [...],
  "visuals": [...],
  "filters": [...],
  "relationships": [...],
  "dashboards": [...]
}
```

## Samples

Place your `.twbx` files in the `samples/` folder for testing.
