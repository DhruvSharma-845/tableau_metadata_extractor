"""
Comprehensive metadata models for Tableau workbook extraction.
Designed for 100% accuracy in metadata capture.
"""

from typing import Optional, List, Dict, Any, Union
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime


class DataType(str, Enum):
    """Tableau data types."""
    STRING = "string"
    INTEGER = "integer"
    REAL = "real"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    SPATIAL = "spatial"
    UNKNOWN = "unknown"


class AggregationType(str, Enum):
    """Tableau aggregation types."""
    SUM = "sum"
    AVG = "avg"
    COUNT = "count"
    COUNTD = "countd"
    MIN = "min"
    MAX = "max"
    MEDIAN = "median"
    ATTR = "attr"
    STDEV = "stdev"
    STDEVP = "stdevp"
    VAR = "var"
    VARP = "varp"
    PERCENTILE = "percentile"
    COLLECT = "collect"
    NONE = "none"


class MarkType(str, Enum):
    """Tableau visualization mark types."""
    BAR = "bar"
    STACKED_BAR = "stacked_bar"
    LINE = "line"
    AREA = "area"
    SQUARE = "square"
    CIRCLE = "circle"
    SHAPE = "shape"
    TEXT = "text"
    MAP = "map"
    PIE = "pie"
    TREEMAP = "treemap"
    GANTT = "gantt"
    POLYGON = "polygon"
    DENSITY = "density"
    HEATMAP = "heatmap"
    HISTOGRAM = "histogram"
    BOX_PLOT = "box_plot"
    AUTOMATIC = "automatic"


class CalculationType(str, Enum):
    """Types of Tableau calculations."""
    SIMPLE = "simple"
    ROW_LEVEL = "row_level"
    AGGREGATE = "aggregate"
    LOD_FIXED = "lod_fixed"
    LOD_INCLUDE = "lod_include"
    LOD_EXCLUDE = "lod_exclude"
    TABLE_CALC = "table_calc"
    COMBINED = "combined"


class FilterType(str, Enum):
    """Types of Tableau filters."""
    CATEGORICAL = "categorical"
    QUANTITATIVE = "quantitative"
    RELATIVE_DATE = "relative_date"
    RANGE = "range"
    TOP_N = "top_n"
    CONDITION = "condition"
    FORMULA = "formula"
    CONTEXT = "context"
    DATA_SOURCE = "data_source"
    EXTRACT = "extract"


class FieldRole(str, Enum):
    """Field role in Tableau."""
    DIMENSION = "dimension"
    MEASURE = "measure"


class FieldMetadata(BaseModel):
    """Complete metadata for a field/column."""
    name: str
    caption: Optional[str] = None
    data_type: DataType = DataType.UNKNOWN
    role: FieldRole = FieldRole.DIMENSION
    default_aggregation: AggregationType = AggregationType.NONE
    is_hidden: bool = False
    
    # Source information
    source_table: Optional[str] = None
    source_column: Optional[str] = None
    
    # Semantic information
    semantic_role: Optional[str] = None  # e.g., "country", "city", "measure"
    geographic_role: Optional[str] = None  # e.g., "State", "Country"
    
    # Format
    default_format: Optional[str] = None
    
    # Usage tracking
    used_in_sheets: List[str] = Field(default_factory=list)
    used_in_calculated_fields: List[str] = Field(default_factory=list)
    
    @property
    def display_name(self) -> str:
        return self.caption or self.name


class CalculatedFieldMetadata(BaseModel):
    """Complete metadata for a calculated field."""
    name: str
    caption: Optional[str] = None
    formula: str
    formula_readable: Optional[str] = None  # Cleaned up version
    
    # Type information
    data_type: DataType = DataType.UNKNOWN
    role: FieldRole = FieldRole.MEASURE
    calculation_type: CalculationType = CalculationType.SIMPLE
    
    # Formula analysis
    aggregations_used: List[str] = Field(default_factory=list)
    functions_used: List[str] = Field(default_factory=list)
    referenced_fields: List[str] = Field(default_factory=list)
    referenced_parameters: List[str] = Field(default_factory=list)
    
    # LOD specific
    lod_type: Optional[str] = None  # FIXED, INCLUDE, EXCLUDE
    lod_dimensions: List[str] = Field(default_factory=list)
    lod_expression: Optional[str] = None
    
    # Table calculation specific
    table_calc_type: Optional[str] = None
    table_calc_direction: Optional[str] = None  # across, down, etc.
    addressing_fields: List[str] = Field(default_factory=list)
    partitioning_fields: List[str] = Field(default_factory=list)
    
    # Complexity
    complexity_score: int = 0
    has_nested_calculations: bool = False
    
    # Usage tracking
    used_in_sheets: List[str] = Field(default_factory=list)
    
    @property
    def display_name(self) -> str:
        return self.caption or self.name
    
    @property
    def is_lod(self) -> bool:
        return self.calculation_type in [
            CalculationType.LOD_FIXED,
            CalculationType.LOD_INCLUDE,
            CalculationType.LOD_EXCLUDE
        ]


class FilterMetadata(BaseModel):
    """Complete metadata for a filter including calculation logic."""
    field: str
    field_caption: Optional[str] = None
    filter_type: FilterType = FilterType.CATEGORICAL
    
    # Scope
    is_context_filter: bool = False
    is_data_source_filter: bool = False
    is_extract_filter: bool = False
    applies_to_worksheets: List[str] = Field(default_factory=list)
    
    # Categorical filter details
    include_values: List[Any] = Field(default_factory=list)
    exclude_values: List[Any] = Field(default_factory=list)
    include_null: bool = True
    
    # Range filter details
    range_min: Optional[Any] = None
    range_max: Optional[Any] = None
    
    # Relative date filter
    relative_date_type: Optional[str] = None  # e.g., "last", "next", "current"
    relative_date_period: Optional[str] = None  # e.g., "days", "weeks", "months"
    relative_date_value: Optional[int] = None
    anchor_date: Optional[str] = None
    
    # Top N filter
    top_n_value: Optional[int] = None
    top_n_field: Optional[str] = None
    top_n_direction: Optional[str] = None  # "top" or "bottom"
    
    # Condition filter
    condition_formula: Optional[str] = None
    condition_aggregation: Optional[str] = None
    condition_comparison: Optional[str] = None
    condition_value: Optional[Any] = None
    
    # Formula filter (custom calculation)
    formula: Optional[str] = None
    
    # Calculation explanation (human-readable)
    calculation_explanation: Optional[str] = None
    
    # Linked filters (for dashboard actions)
    linked_to_dashboard: Optional[str] = None
    source_worksheet: Optional[str] = None


class AxisMetadata(BaseModel):
    """Metadata for chart axes."""
    axis_type: str = Field(description="'x', 'y', 'x2', 'y2'")
    field: Optional[str] = None
    field_caption: Optional[str] = None
    aggregation: Optional[AggregationType] = None
    
    # Scale
    scale_type: str = "linear"  # linear, log, reversed
    include_zero: bool = True
    
    # Range
    range_min: Optional[float] = None
    range_max: Optional[float] = None
    range_auto: bool = True
    
    # Formatting
    title: Optional[str] = None
    title_visible: bool = True
    tick_interval: Optional[float] = None
    format_string: Optional[str] = None
    
    # Grid
    major_grid_lines: bool = True
    minor_grid_lines: bool = False


class VisualMetadata(BaseModel):
    """Complete metadata for a visualization."""
    sheet_name: str
    chart_type: MarkType = MarkType.AUTOMATIC
    chart_type_inferred: Optional[str] = None  # More specific type
    
    # Encodings
    rows: List[Dict[str, Any]] = Field(default_factory=list)
    columns: List[Dict[str, Any]] = Field(default_factory=list)
    color: Optional[Dict[str, Any]] = None
    size: Optional[Dict[str, Any]] = None
    shape: Optional[Dict[str, Any]] = None
    label: List[Dict[str, Any]] = Field(default_factory=list)
    detail: List[Dict[str, Any]] = Field(default_factory=list)
    tooltip: List[Dict[str, Any]] = Field(default_factory=list)
    path: Optional[Dict[str, Any]] = None  # For line ordering
    
    # Axes
    x_axis: Optional[AxisMetadata] = None
    y_axis: Optional[AxisMetadata] = None
    secondary_x_axis: Optional[AxisMetadata] = None
    secondary_y_axis: Optional[AxisMetadata] = None
    
    # Size
    width: Optional[int] = None
    height: Optional[int] = None
    fixed_size: bool = False
    
    # Marks
    mark_color: Optional[str] = None
    mark_size: Optional[float] = None
    mark_shape: Optional[str] = None
    mark_opacity: Optional[float] = None
    
    # Dual axis
    is_dual_axis: bool = False
    synchronized_axes: bool = False
    
    # Reference lines
    reference_lines: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Trend lines
    trend_lines: List[Dict[str, Any]] = Field(default_factory=list)


class SheetMetadata(BaseModel):
    """Complete metadata for a worksheet."""
    name: str
    title: Optional[str] = None
    
    # Data source
    datasource_name: Optional[str] = None
    datasource_caption: Optional[str] = None
    
    # Visual configuration
    visual: Optional[VisualMetadata] = None
    
    # Fields used
    all_fields_used: List[str] = Field(default_factory=list)
    dimensions_used: List[str] = Field(default_factory=list)
    measures_used: List[str] = Field(default_factory=list)
    calculated_fields_used: List[str] = Field(default_factory=list)
    parameters_used: List[str] = Field(default_factory=list)
    
    # Filters
    filters: List[FilterMetadata] = Field(default_factory=list)
    quick_filters: List[str] = Field(default_factory=list)  # Exposed as UI filters
    
    # Sorting
    sort_fields: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Tooltip
    tooltip_sheets: List[str] = Field(default_factory=list)  # Viz in tooltip
    custom_tooltip: Optional[str] = None
    
    # Actions this sheet participates in
    source_for_actions: List[str] = Field(default_factory=list)
    target_for_actions: List[str] = Field(default_factory=list)
    
    # Dashboard membership
    used_in_dashboards: List[str] = Field(default_factory=list)
    
    # Hidden
    is_hidden: bool = False


class DashboardZoneMetadata(BaseModel):
    """Metadata for a zone/object on a dashboard."""
    zone_id: Optional[str] = None
    zone_type: str = Field(description="'worksheet', 'text', 'image', 'web', 'blank', 'container', 'filter', 'parameter', 'legend'")
    name: Optional[str] = None
    
    # For worksheet zones
    worksheet_name: Optional[str] = None
    
    # For text zones
    text_content: Optional[str] = None
    
    # For image zones
    image_path: Optional[str] = None
    
    # For web zones
    web_url: Optional[str] = None
    
    # Position (in pixels)
    x: float = 0
    y: float = 0
    width: float = 100
    height: float = 100
    
    # Layout
    z_order: int = 0
    is_floating: bool = False
    is_visible: bool = True
    
    # Container info
    parent_container: Optional[str] = None
    child_zones: List[str] = Field(default_factory=list)
    layout_direction: Optional[str] = None  # horizontal, vertical


class DashboardActionMetadata(BaseModel):
    """Metadata for dashboard actions."""
    name: str
    action_type: str = Field(description="'filter', 'highlight', 'url', 'parameter', 'sheet_navigation'")
    
    # Trigger
    trigger: str = "select"  # select, hover, menu
    
    # Source
    source_worksheets: List[str] = Field(default_factory=list)
    source_fields: List[str] = Field(default_factory=list)
    
    # Target
    target_worksheets: List[str] = Field(default_factory=list)
    target_fields: List[str] = Field(default_factory=list)
    
    # For URL actions
    url_template: Optional[str] = None
    url_target: Optional[str] = None  # new tab, same window
    
    # For parameter actions
    target_parameter: Optional[str] = None
    parameter_field: Optional[str] = None
    
    # Clearing selection
    clear_selection_type: str = "keep"  # keep, leave, show_all


class DashboardMetadata(BaseModel):
    """Complete metadata for a dashboard."""
    name: str
    title: Optional[str] = None
    
    # Size
    width: int = 1000
    height: int = 800
    device_type: str = "desktop"  # desktop, tablet, phone
    
    # Zones/Objects
    zones: List[DashboardZoneMetadata] = Field(default_factory=list)
    
    # Worksheets used
    worksheets: List[str] = Field(default_factory=list)
    
    # Actions
    actions: List[DashboardActionMetadata] = Field(default_factory=list)
    
    # Filters shown on dashboard
    exposed_filters: List[str] = Field(default_factory=list)
    
    # Parameters shown on dashboard
    exposed_parameters: List[str] = Field(default_factory=list)
    
    # Layout
    layout_type: str = "tiled"  # tiled, floating


class ParameterMetadata(BaseModel):
    """Complete metadata for a parameter."""
    name: str
    caption: Optional[str] = None
    data_type: DataType = DataType.STRING
    
    # Current value
    current_value: Optional[Any] = None
    
    # Allowable values
    allowable_values_type: str = "all"  # all, list, range
    allowable_values: List[Any] = Field(default_factory=list)
    
    # Range constraints
    range_min: Optional[Any] = None
    range_max: Optional[Any] = None
    step_size: Optional[float] = None
    
    # Display
    display_format: Optional[str] = None
    
    # Usage tracking
    used_in_calculated_fields: List[str] = Field(default_factory=list)
    used_in_filters: List[str] = Field(default_factory=list)
    used_in_sheets: List[str] = Field(default_factory=list)
    exposed_on_dashboards: List[str] = Field(default_factory=list)
    
    @property
    def display_name(self) -> str:
        return self.caption or self.name


class DataSourceMetadata(BaseModel):
    """Complete metadata for a data source."""
    name: str
    caption: Optional[str] = None
    
    # Connection
    connection_type: str = "unknown"
    connection_class: Optional[str] = None
    server: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    schema_name: Optional[str] = None
    
    # Tables
    tables: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Joins
    joins: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Relationships (new data model)
    relationships: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Custom SQL
    custom_sql: Optional[str] = None
    
    # Fields
    fields: List[FieldMetadata] = Field(default_factory=list)
    calculated_fields: List[CalculatedFieldMetadata] = Field(default_factory=list)
    
    # Extract info
    has_extract: bool = False
    extract_filters: List[FilterMetadata] = Field(default_factory=list)
    
    @property
    def display_name(self) -> str:
        return self.caption or self.name


class RelationshipMetadata(BaseModel):
    """Metadata describing relationships between elements."""
    relationship_type: str = Field(description="'field_to_sheet', 'calc_to_field', 'sheet_to_dashboard', 'filter_to_sheet', 'action', 'parameter'")
    
    # Source
    source_type: str  # field, calculated_field, sheet, dashboard, filter, parameter
    source_name: str
    
    # Target
    target_type: str
    target_name: str
    
    # Details
    relationship_details: Dict[str, Any] = Field(default_factory=dict)
    
    # Description
    description: Optional[str] = None


class WorkbookMetadata(BaseModel):
    """Complete metadata for a Tableau workbook."""
    # Basic info
    name: str
    version: Optional[str] = None
    build: Optional[str] = None
    
    # Source
    source_file: Optional[str] = None
    extraction_timestamp: Optional[datetime] = None
    extraction_method: str = "xml"  # xml or api
    
    # Data sources
    datasources: List[DataSourceMetadata] = Field(default_factory=list)
    
    # Sheets
    sheets: List[SheetMetadata] = Field(default_factory=list)
    
    # Dashboards
    dashboards: List[DashboardMetadata] = Field(default_factory=list)
    
    # Parameters
    parameters: List[ParameterMetadata] = Field(default_factory=list)
    
    # All relationships (aggregated view)
    relationships: List[RelationshipMetadata] = Field(default_factory=list)
    
    # Summary statistics
    total_sheets: int = 0
    total_dashboards: int = 0
    total_fields: int = 0
    total_calculated_fields: int = 0
    total_parameters: int = 0
    total_filters: int = 0
    
    # Validation
    validation_errors: List[str] = Field(default_factory=list)
    validation_warnings: List[str] = Field(default_factory=list)
    
    def compute_statistics(self):
        """Compute summary statistics."""
        self.total_sheets = len(self.sheets)
        self.total_dashboards = len(self.dashboards)
        self.total_parameters = len(self.parameters)
        
        total_fields = 0
        total_calc = 0
        total_filters = 0
        
        for ds in self.datasources:
            total_fields += len(ds.fields)
            total_calc += len(ds.calculated_fields)
        
        for sheet in self.sheets:
            total_filters += len(sheet.filters)
        
        self.total_fields = total_fields
        self.total_calculated_fields = total_calc
        self.total_filters = total_filters
    
    def to_json(self, indent: int = 2) -> str:
        """Export to JSON."""
        return self.model_dump_json(indent=indent)
    
    def to_dict(self) -> Dict[str, Any]:
        """Export to dictionary."""
        return self.model_dump()
