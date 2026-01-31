# Tableau Metadata Extractor - Technical Explanation

## Table of Contents
1. [How Tableau Stores Metadata](#how-tableau-stores-metadata)
2. [Extraction Process](#extraction-process)
3. [Data Models Explained](#data-models-explained)
4. [Calculated Fields Analysis](#calculated-fields-analysis)
5. [Filter Logic Parsing](#filter-logic-parsing)
6. [Visual Type Detection](#visual-type-detection)
7. [Relationship Mapping](#relationship-mapping)
8. [Option A vs Option C](#option-a-vs-option-c)

---

## How Tableau Stores Metadata

### TWBX vs TWB

| File Type | Description | Structure |
|-----------|-------------|-----------|
| **.twbx** | Tableau Packaged Workbook | ZIP archive containing TWB + data extracts + images |
| **.twb** | Tableau Workbook | Plain XML file with all definitions |

### Key XML Elements in TWB

```
workbook
├── datasources                 # All data connections
│   └── datasource
│       ├── connection          # Server, database, auth
│       ├── column              # Field definitions
│       │   └── calculation     # Formula for calculated fields
│       └── relation            # Tables and joins
│
├── worksheets                  # All sheets/visualizations
│   └── worksheet
│       ├── table
│       │   ├── rows            # Fields on rows shelf
│       │   ├── cols            # Fields on columns shelf
│       │   └── panes
│       │       └── pane
│       │           ├── mark    # Visualization type (bar, line, etc.)
│       │           └── encoding # Color, size, shape, label, etc.
│       └── filter              # Applied filters
│
├── dashboards                  # Dashboard layouts
│   └── dashboard
│       ├── size                # Width, height
│       ├── zones               # Layout containers
│       │   └── zone            # Individual objects (worksheets, text, etc.)
│       └── actions             # Interactivity (filter, highlight, URL)
│
└── datasource[@name='Parameters']  # Parameters defined in workbook
```

---

## Extraction Process

### Step 1: File Handling

```python
# If .twbx (packaged)
if file.endswith('.twbx'):
    # Extract ZIP to temp directory
    with zipfile.ZipFile(file_path) as z:
        z.extractall(temp_dir)
    # Find the .twb file inside
    twb_path = find_twb_in_directory(temp_dir)
else:
    # Direct .twb file
    twb_path = file_path
```

### Step 2: XML Parsing

```python
from lxml import etree

# Parse XML tree
tree = etree.parse(twb_path)
root = tree.getroot()

# Extract version info
version = root.get("version")
build = root.get("source-build")
```

### Step 3: Data Source Extraction

For each `<datasource>` element:

```python
for ds_elem in root.findall(".//datasource"):
    name = ds_elem.get("name")
    caption = ds_elem.get("caption")  # User-friendly name
    
    # Parse connection
    conn = ds_elem.find(".//connection")
    connection_type = conn.get("class")
    server = conn.get("server")
    database = conn.get("dbname")
    
    # Parse fields
    for col in ds_elem.findall(".//column"):
        field_name = col.get("name")
        datatype = col.get("datatype")
        role = col.get("role")  # dimension or measure
        
        # Check for calculation (makes it a calculated field)
        calc = col.find(".//calculation")
        if calc is not None:
            formula = calc.get("formula")
```

### Step 4: Worksheet Extraction

For each `<worksheet>` element:

```python
for ws_elem in root.findall(".//worksheet"):
    name = ws_elem.get("name")
    
    # Get mark type
    mark = ws_elem.find(".//panes//mark")
    chart_type = mark.get("class")  # bar, line, area, etc.
    
    # Get rows/columns
    rows = ws_elem.find(".//rows").text  # e.g., "[Category]"
    cols = ws_elem.find(".//cols").text  # e.g., "[SUM(Sales)]"
    
    # Get encodings
    for encoding in ws_elem.findall(".//encoding"):
        attr = encoding.get("attr")    # color, size, shape
        column = encoding.get("column") # [Field Name]
    
    # Get filters
    for filter_elem in ws_elem.findall(".//filter"):
        field = filter_elem.get("column")
        # Parse filter logic...
```

### Step 5: Dashboard Extraction

For each `<dashboard>` element:

```python
for dash_elem in root.findall(".//dashboard"):
    name = dash_elem.get("name")
    
    # Get size
    size = dash_elem.find(".//size")
    width = size.get("maxwidth")
    height = size.get("maxheight")
    
    # Get zones (layout objects)
    for zone in dash_elem.findall(".//zone"):
        zone_name = zone.get("name")      # Worksheet name if viz
        zone_type = zone.get("type")      # text, web, image, etc.
        x, y = zone.get("x"), zone.get("y")
        w, h = zone.get("w"), zone.get("h")
    
    # Get actions
    for action in dash_elem.findall(".//action"):
        action_name = action.get("name")
        action_type = action.get("type")  # filter, highlight, url
```

### Step 6: Relationship Building

After parsing all components, we build relationships:

```python
# Field → Sheet: Which fields are used in which sheets
for sheet in sheets:
    for field in sheet.all_fields_used:
        relationships.append({
            "type": "field_to_sheet",
            "source": field,
            "target": sheet.name
        })

# Calc → Field: Which fields are referenced in calculations
for calc in calculated_fields:
    for ref_field in calc.referenced_fields:
        relationships.append({
            "type": "calc_to_field",
            "source": calc.name,
            "target": ref_field
        })

# Sheet → Dashboard: Which sheets are in which dashboards
for dashboard in dashboards:
    for worksheet in dashboard.worksheets:
        relationships.append({
            "type": "sheet_to_dashboard",
            "source": worksheet,
            "target": dashboard.name
        })
```

---

## Data Models Explained

### Core Hierarchy

```
WorkbookMetadata
├── datasources: List[DataSourceMetadata]
│   ├── fields: List[FieldMetadata]
│   └── calculated_fields: List[CalculatedFieldMetadata]
├── sheets: List[SheetMetadata]
│   ├── visual: VisualMetadata
│   └── filters: List[FilterMetadata]
├── dashboards: List[DashboardMetadata]
│   ├── zones: List[DashboardZoneMetadata]
│   └── actions: List[DashboardActionMetadata]
├── parameters: List[ParameterMetadata]
└── relationships: List[RelationshipMetadata]
```

### Field Types

| Field Type | Example | Role |
|------------|---------|------|
| **Dimension** | Category, Region, Date | Categorical grouping |
| **Measure** | Sales, Profit, Quantity | Numeric aggregation |
| **Calculated** | Profit Ratio, YTD Sales | Derived from formula |
| **Parameter** | Date Range, Top N | User input |

### Data Types

| Tableau Type | Description | Example |
|--------------|-------------|---------|
| `string` | Text | "California" |
| `integer` | Whole numbers | 42 |
| `real` | Decimal numbers | 3.14159 |
| `boolean` | True/False | TRUE |
| `date` | Date only | 2026-01-31 |
| `datetime` | Date and time | 2026-01-31 12:30:00 |

---

## Calculated Fields Analysis

### Formula Parsing

The extractor analyzes each formula to determine:

1. **Calculation Type**
   - `simple` - Row-level calculation (e.g., `[Price] * [Quantity]`)
   - `aggregate` - Contains aggregation (e.g., `SUM([Sales])`)
   - `lod_fixed` - FIXED LOD expression
   - `lod_include` - INCLUDE LOD expression
   - `lod_exclude` - EXCLUDE LOD expression
   - `table_calc` - Table calculation (e.g., `RUNNING_SUM`)

2. **Functions Used**
   - Extracted via regex: `FUNCTION_NAME\s*\(`
   - Categorized: aggregate, string, date, logical, math

3. **Referenced Fields**
   - Extracted via regex: `\[([^\]]+)\]`
   - Used for dependency tracking

4. **Complexity Score** (0-100)
   - +30 for LOD expressions
   - +40 for table calculations
   - +5-10 for nested IF/CASE
   - +15 for deeply nested formulas

### Example Analysis

```python
formula = "{FIXED [Customer ID] : SUM([Sales])}"

analysis = {
    "calculation_type": "lod_fixed",
    "lod_type": "FIXED",
    "lod_dimensions": ["Customer ID"],
    "lod_expression": "SUM([Sales])",
    "aggregations_used": ["SUM"],
    "functions_used": ["SUM"],
    "referenced_fields": ["Customer ID", "Sales"],
    "complexity_score": 40
}
```

### LOD Expression Types

| Type | Syntax | Description |
|------|--------|-------------|
| **FIXED** | `{FIXED [Dim] : AGG([Measure])}` | Calculate at specified dimension level |
| **INCLUDE** | `{INCLUDE [Dim] : AGG([Measure])}` | Add dimension to current level |
| **EXCLUDE** | `{EXCLUDE [Dim] : AGG([Measure])}` | Remove dimension from current level |

---

## Filter Logic Parsing

### Filter Types

| Type | XML Pattern | Example |
|------|-------------|---------|
| **Categorical** | `<groupfilter function="member">` | Show only "West" region |
| **Range** | `<range min="..." max="...">` | Sales between 1000-5000 |
| **Relative Date** | `<relative-date type="last" period="days">` | Last 30 days |
| **Top N** | `<top type="top" value="10">` | Top 10 products |
| **Condition** | `<condition formula="...">` | Where profit > 0 |
| **Formula** | `<calculation formula="...">` | Custom TRUE/FALSE logic |

### Parsing Examples

#### Categorical Filter
```xml
<filter column="[Region]">
  <groupfilter function="union">
    <groupfilter function="member" member="'West'"/>
    <groupfilter function="member" member="'East'"/>
  </groupfilter>
</filter>
```
**Explanation:** `Show records where [Region] is one of: 'West', 'East'`

#### Range Filter
```xml
<filter column="[Sales]">
  <range min="1000" max="5000"/>
</filter>
```
**Explanation:** `Show records where [Sales] is between 1000 and 5000`

#### Relative Date Filter
```xml
<filter column="[Order Date]">
  <relative-date type="last" period="days" value="30"/>
</filter>
```
**Explanation:** `Show records from the last 30 days`

#### Top N Filter
```xml
<filter column="[Product]">
  <top type="top" value="10" column="[Sales]"/>
</filter>
```
**Explanation:** `Show top 10 values of [Product] by [Sales]`

### Human-Readable Explanations

The extractor generates plain English explanations for each filter:

```python
def generate_filter_explanation(filter):
    if filter.type == "categorical":
        if filter.include_values:
            return f"Show records where [{filter.field}] is one of: {filter.include_values}"
        elif filter.exclude_values:
            return f"Exclude records where [{filter.field}] is: {filter.exclude_values}"
    
    elif filter.type == "range":
        return f"Show records where [{filter.field}] is between {filter.min} and {filter.max}"
    
    elif filter.type == "relative_date":
        return f"Show records from the {filter.relative_type} {filter.value} {filter.period}"
    
    elif filter.type == "top_n":
        return f"Show {filter.direction} {filter.value} values of [{filter.field}] by {filter.by_field}"
```

---

## Visual Type Detection

### Mark Types

| Tableau Mark | Chart Type | Detection |
|--------------|------------|-----------|
| `bar` | Bar Chart | `<mark class="bar"/>` |
| `line` | Line Chart | `<mark class="line"/>` |
| `area` | Area Chart | `<mark class="area"/>` |
| `circle` | Scatter Plot | `<mark class="circle"/>` |
| `square` | Heat Map | `<mark class="square"/>` |
| `text` | Text Table | `<mark class="text"/>` |
| `map` | Map | `<mark class="map"/>` |
| `pie` | Pie Chart | `<mark class="pie"/>` |
| `ganttBar` | Gantt Chart | `<mark class="ganttBar"/>` |
| `polygon` | Filled Map | `<mark class="polygon"/>` |
| `Automatic` | Auto-detect | `<mark class="Automatic"/>` |

### Inferred Chart Types

Beyond the basic mark, we infer more specific chart types:

```python
def infer_chart_type(mark_type, rows, columns):
    if mark_type == "bar":
        # Check if horizontal (measures on rows)
        if any(has_aggregation(r) for r in rows):
            return "horizontal_bar"
        return "vertical_bar"
    
    elif mark_type == "line":
        # Check for date on x-axis
        if any(is_date_field(c) for c in columns):
            return "time_series"
        return "line_chart"
    
    elif mark_type == "circle":
        # Check for two measures = scatter
        measure_count = sum(1 for c in columns + rows if is_measure(c))
        if measure_count >= 2:
            return "scatter_plot"
        return "bubble_chart"
```

### Visual Encodings

| Encoding | Purpose | XML Path |
|----------|---------|----------|
| **Rows** | Y-axis grouping | `//table/rows` |
| **Columns** | X-axis grouping | `//table/cols` |
| **Color** | Color by field | `//encoding[@attr='color']` |
| **Size** | Size by measure | `//encoding[@attr='size']` |
| **Shape** | Shape by dimension | `//encoding[@attr='shape']` |
| **Label** | Text labels | `//encoding[@attr='text']` |
| **Detail** | Level of detail | `//encoding[@attr='lod']` |
| **Tooltip** | Hover info | `//encoding[@attr='tooltip']` |
| **Path** | Line ordering | `//encoding[@attr='path']` |

---

## Relationship Mapping

### Relationship Types

| Type | Description | Example |
|------|-------------|---------|
| `field_to_sheet` | Field used in worksheet | Sales → Revenue Chart |
| `calc_to_field` | Calculated field references field | Profit Ratio → Sales, Profit |
| `sheet_to_dashboard` | Worksheet in dashboard | Revenue Chart → Executive Dashboard |
| `action` | Dashboard action link | Sheet1 → Sheet2 (filter action) |
| `parameter` | Parameter used in calculation | Date Parameter → Date Filter Calc |

### Building the Relationship Graph

```python
relationships = []

# 1. Field → Sheet relationships
for sheet in sheets:
    for field in sheet.all_fields_used:
        relationships.append(RelationshipMetadata(
            relationship_type="field_to_sheet",
            source_type="field",
            source_name=field,
            target_type="sheet",
            target_name=sheet.name,
            description=f"Field '{field}' is used in sheet '{sheet.name}'"
        ))

# 2. Calculated Field → Referenced Field relationships
for calc in calculated_fields:
    for ref_field in calc.referenced_fields:
        relationships.append(RelationshipMetadata(
            relationship_type="calc_to_field",
            source_type="calculated_field",
            source_name=calc.name,
            target_type="field",
            target_name=ref_field,
            description=f"Calc '{calc.name}' references '{ref_field}'"
        ))

# 3. Sheet → Dashboard relationships
for dashboard in dashboards:
    for worksheet in dashboard.worksheets:
        relationships.append(RelationshipMetadata(
            relationship_type="sheet_to_dashboard",
            source_type="sheet",
            source_name=worksheet,
            target_type="dashboard",
            target_name=dashboard.name,
            description=f"Sheet '{worksheet}' is in dashboard '{dashboard.name}'"
        ))

# 4. Action relationships
for dashboard in dashboards:
    for action in dashboard.actions:
        for source_ws in action.source_worksheets:
            for target_ws in action.target_worksheets:
                relationships.append(RelationshipMetadata(
                    relationship_type="action",
                    source_type="sheet",
                    source_name=source_ws,
                    target_type="sheet",
                    target_name=target_ws,
                    relationship_details={
                        "action_name": action.name,
                        "action_type": action.action_type
                    }
                ))
```

### Relationship Visualization

```
┌─────────────┐         ┌─────────────┐
│   Sales     │────────▶│ Revenue by  │
│   (field)   │         │   Region    │
└─────────────┘         │  (sheet)    │
                        └──────┬──────┘
                               │
┌─────────────┐                │
│   Profit    │────────────────┤
│   (field)   │                │
└─────────────┘                │
                               ▼
┌─────────────┐         ┌─────────────┐
│Profit Ratio │         │  Executive  │
│   (calc)    │────────▶│  Dashboard  │
└──────┬──────┘         └──────┬──────┘
       │                       │
       ▼                       │ (filter action)
┌─────────────┐                │
│  Sales,     │◀───────────────┘
│  Profit     │
└─────────────┘
```

---

## Option A vs Option C

### Option A: XML Parser

**How it works:**
1. Extract .twbx ZIP file
2. Parse .twb XML directly
3. Navigate XML tree to extract all metadata
4. Build Pydantic models from parsed data

**Advantages:**
- 100% accuracy - direct source parsing
- Works offline
- No authentication required
- Complete formula access
- All pixel positions available

**Limitations:**
- Only works with local files
- Cannot get server-specific metadata (usage stats, etc.)

### Option C: Metadata API

**How it works:**
1. Authenticate with Tableau Server (PAT or username/password)
2. Send GraphQL queries to Metadata API endpoint
3. Parse response JSON
4. Build Pydantic models from API data

**GraphQL Query Example:**
```graphql
query GetWorkbookFields($workbookLuid: String!) {
  embeddedDatasources(filter: {workbook: {luid: $workbookLuid}}) {
    name
    fields {
      name
      dataType
      role
      isCalculated
      formula
      aggregation
    }
  }
}
```

**Advantages:**
- Works with published workbooks
- Can access multiple workbooks programmatically
- Gets server-side metadata (usage, permissions)
- Supports site-wide governance

**Limitations:**
- Requires Tableau Server/Online access
- Authentication required
- Some metadata not exposed via API
- ~95% accuracy (some details not available)

### Comparison Matrix

| Feature | Option A (XML) | Option C (API) |
|---------|----------------|----------------|
| Accuracy | 100% | ~95% |
| Offline | ✅ | ❌ |
| Server Required | ❌ | ✅ |
| Full Formulas | ✅ | ⚠️ Partial |
| Pixel Positions | ✅ | ❌ |
| Filter Details | ✅ | ⚠️ Limited |
| Axis Config | ✅ | ❌ |
| Actions | ✅ | ⚠️ Limited |
| Usage Stats | ❌ | ✅ |
| Permissions | ❌ | ✅ |
| Bulk Processing | Manual | ✅ |

### When to Use Each

**Use Option A (XML) when:**
- Analyzing local workbook files
- Need 100% accurate metadata
- Migrating to another BI platform
- Need filter/axis/layout details

**Use Option C (API) when:**
- Governing published workbooks
- Building server-wide lineage
- Need usage/permission metadata
- Processing multiple workbooks at scale

**Use Both (Comparison) when:**
- Validating extraction accuracy
- Ensuring published matches local
- Auditing metadata completeness
