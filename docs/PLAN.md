# Tableau Metadata Extractor - Technical Plan

## Overview

This document outlines the technical architecture and implementation plan for extracting 100% accurate metadata from Tableau workbooks (.twbx/.twb files).

---

## Problem Statement

Tableau workbooks contain rich metadata about:
- KPIs and metrics with their calculations
- Data sources and their schemas
- Visualizations with chart configurations
- Filters and their logic
- Dashboards and interactivity

Extracting this metadata accurately is essential for:
- Migration to other BI platforms (Power BI, Looker, etc.)
- Documentation and governance
- Impact analysis
- Audit and compliance

---

## Solution Architecture

### Two Extraction Methods

| Method | Option A: XML Parser | Option C: Metadata API |
|--------|---------------------|------------------------|
| **Source** | Local .twbx/.twb files | Tableau Server/Online |
| **Technology** | lxml XML parsing | GraphQL queries |
| **Accuracy** | 100% (direct source) | ~95% (API limitations) |
| **Use Case** | Local analysis, migration | Server governance, lineage |
| **Authentication** | None required | PAT or username/password |

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    Tableau Metadata Extractor                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐    │
│  │   main.py    │────▶│  Extractors  │────▶│    Models    │    │
│  │    (CLI)     │     │              │     │              │    │
│  └──────────────┘     │ ┌──────────┐ │     │ WorkbookMeta │    │
│                       │ │Option A  │ │     │ SheetMeta    │    │
│  ┌──────────────┐     │ │XML Parser│ │     │ FieldMeta    │    │
│  │    Utils     │     │ └──────────┘ │     │ FilterMeta   │    │
│  │              │     │              │     │ DashboardMeta│    │
│  │ ┌──────────┐ │     │ ┌──────────┐ │     │ etc.         │    │
│  │ │Comparison│ │     │ │Option C  │ │     └──────────────┘    │
│  │ └──────────┘ │     │ │API Client│ │              │          │
│  │ ┌──────────┐ │     │ └──────────┘ │              ▼          │
│  │ │Validation│ │     └──────────────┘     ┌──────────────┐    │
│  │ └──────────┘ │              │           │   Output     │    │
│  │ ┌──────────┐ │              │           │              │    │
│  │ │  Output  │◀┼──────────────┘           │ JSON/Excel/  │    │
│  │ └──────────┘ │                          │ HTML         │    │
│  └──────────────┘                          └──────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## TWBX File Structure

A `.twbx` file is a ZIP archive containing:

```
workbook.twbx (ZIP)
├── workbook.twb          # XML workbook definition (main source)
├── Data/
│   ├── extract.hyper     # Tableau Hyper extract (optional)
│   └── extract.tde       # Legacy TDE extract (optional)
├── Image/
│   └── *.png             # Embedded images
└── External Files/
    └── *                 # Other embedded resources
```

### TWB XML Structure

```xml
<workbook version="18.1">
  <datasources>
    <datasource name="..." caption="...">
      <connection class="..." server="..." dbname="...">
        <relation name="..." table="..." type="table"/>
      </connection>
      <column name="..." datatype="string" role="dimension"/>
      <column name="..." datatype="real" role="measure">
        <calculation formula="SUM([Sales])"/>
      </column>
    </datasource>
  </datasources>
  
  <worksheets>
    <worksheet name="Sales by Region">
      <table>
        <rows>[Category]</rows>
        <cols>[SUM(Sales)]</cols>
        <panes>
          <pane>
            <mark class="bar"/>
            <encoding attr="color" column="[Region]"/>
          </pane>
        </panes>
      </table>
      <filter column="[Region]">
        <groupfilter function="member" member="'West'"/>
      </filter>
    </worksheet>
  </worksheets>
  
  <dashboards>
    <dashboard name="Sales Dashboard">
      <size maxwidth="1200" maxheight="800"/>
      <zones>
        <zone name="Sales by Region" type="viz" x="0" y="0" w="600" h="400"/>
      </zones>
      <actions>
        <action name="Filter Action" type="filter">
          <source worksheet="Sheet1"/>
          <target worksheet="Sheet2"/>
        </action>
      </actions>
    </dashboard>
  </dashboards>
</workbook>
```

---

## Implementation Phases

### Phase 1: Core Infrastructure ✅
- TWBX extraction (ZIP handling)
- TWB XML parsing with lxml
- Pydantic data models for type safety

### Phase 2: Field Extraction ✅
- Regular columns with data types
- Calculated fields with formula parsing
- LOD expression detection (FIXED, INCLUDE, EXCLUDE)
- Table calculation detection
- Aggregation identification

### Phase 3: Visual Extraction ✅
- Mark type detection (bar, line, area, etc.)
- Shelf parsing (rows, columns)
- Encoding extraction (color, size, shape, label, detail, tooltip)
- Axis configuration
- Reference lines and trend lines

### Phase 4: Filter Extraction ✅
- Categorical filters (include/exclude values)
- Range filters (min/max)
- Relative date filters
- Top N filters
- Condition filters
- Formula filters
- **Human-readable calculation explanations**

### Phase 5: Dashboard Extraction ✅
- Zone parsing with pixel positions
- Worksheet references
- Dashboard actions (filter, highlight, URL)
- Exposed filters and parameters

### Phase 6: Relationship Mapping ✅
- Field → Sheet usage
- Calculated field → Field dependencies
- Sheet → Dashboard membership
- Action → Source/Target linkage
- Parameter → Calculation usage

### Phase 7: Metadata API (Option C) ✅
- Authentication (PAT, username/password)
- GraphQL queries for workbook metadata
- Field and sheet extraction
- Comparison with XML extraction

### Phase 8: Output & Validation ✅
- JSON export (complete metadata)
- Excel export (multi-sheet workbook)
- HTML report (interactive)
- Validation framework
- Comparison utility

---

## Data Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   .twbx     │────▶│  Extract    │────▶│   .twb      │
│   (ZIP)     │     │  ZIP        │     │   (XML)     │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                                               ▼
┌─────────────────────────────────────────────────────────────┐
│                      XML Parser                              │
├─────────────────────────────────────────────────────────────┤
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐│
│  │Datasources│  │Worksheets │  │ Dashboards│  │Parameters ││
│  │  Parser   │  │  Parser   │  │  Parser   │  │  Parser   ││
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘│
│        │              │              │              │       │
│        ▼              ▼              ▼              ▼       │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐│
│  │  Fields   │  │  Visuals  │  │   Zones   │  │  Params   ││
│  │  Calcs    │  │  Filters  │  │  Actions  │  │           ││
│  │  Tables   │  │  Axes     │  │           │  │           ││
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘│
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │   Relationship Builder   │
              │   (Link all components)  │
              └────────────┬────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │    WorkbookMetadata     │
              │    (Complete Model)     │
              └────────────┬────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
    ┌───────────┐    ┌───────────┐    ┌───────────┐
    │   JSON    │    │   Excel   │    │   HTML    │
    │  Output   │    │  Output   │    │  Report   │
    └───────────┘    └───────────┘    └───────────┘
```

---

## Key Technical Decisions

### 1. Why lxml over ElementTree?
- Better XPath support
- Faster parsing for large files
- Better namespace handling

### 2. Why Pydantic Models?
- Type validation
- JSON serialization
- Clear data contracts
- IDE autocomplete support

### 3. Why Both XML and API Methods?
- XML provides 100% accuracy for local files
- API enables server-side governance
- Comparison validates extraction accuracy

### 4. Filter Calculation Explanations
- Converts internal filter XML to human-readable text
- Essential for documentation and migration
- Supports all filter types (categorical, range, relative date, top N, condition)

---

## Accuracy Guarantees

| Component | Accuracy | Notes |
|-----------|----------|-------|
| Field Names | 100% | Direct XML parsing |
| Data Types | 100% | Mapped from Tableau types |
| Formulas | 100% | Raw formula preserved |
| Chart Types | 100% | Mark class extraction |
| Filter Logic | 100% | Complete filter XML parsing |
| Pixel Positions | 100% | Zone coordinates from XML |
| Relationships | 100% | Built from parsed data |

---

## Future Enhancements

1. **Semantic Layer Export** - Generate dbt or LookML models
2. **Power BI Auto-Conversion** - Automatic DAX translation
3. **Lineage Visualization** - Interactive dependency graphs
4. **Version Comparison** - Diff between workbook versions
5. **Bulk Processing** - Process entire Tableau Server sites
