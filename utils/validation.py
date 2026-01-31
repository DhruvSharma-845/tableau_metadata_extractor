"""
Validation framework for Tableau metadata extraction.

Validates the completeness and accuracy of extracted metadata.
"""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

from models.metadata_models import (
    WorkbookMetadata,
    DataSourceMetadata,
    SheetMetadata,
    DashboardMetadata,
    FieldMetadata,
    CalculatedFieldMetadata,
    FilterMetadata,
    VisualMetadata,
)


class ValidationLevel(str, Enum):
    """Validation severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    """Represents a validation issue."""
    level: ValidationLevel
    category: str
    item: str
    message: str
    suggestion: Optional[str] = None
    path: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of metadata validation."""
    is_valid: bool = True
    issues: List[ValidationIssue] = field(default_factory=list)
    warnings_count: int = 0
    errors_count: int = 0
    critical_count: int = 0
    checked_items: int = 0
    passed_items: int = 0
    
    def add_issue(self, issue: ValidationIssue):
        """Add a validation issue."""
        self.issues.append(issue)
        
        if issue.level == ValidationLevel.WARNING:
            self.warnings_count += 1
        elif issue.level == ValidationLevel.ERROR:
            self.errors_count += 1
            self.is_valid = False
        elif issue.level == ValidationLevel.CRITICAL:
            self.critical_count += 1
            self.is_valid = False
    
    def get_score(self) -> float:
        """Calculate a validation score (0-100)."""
        if self.checked_items == 0:
            return 100.0
        
        # Calculate based on issues and checks
        issue_penalty = (
            self.critical_count * 20 +
            self.errors_count * 10 +
            self.warnings_count * 2
        )
        
        score = max(0, 100 - issue_penalty)
        return round(score, 1)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_valid": self.is_valid,
            "score": self.get_score(),
            "checked_items": self.checked_items,
            "passed_items": self.passed_items,
            "issues_summary": {
                "critical": self.critical_count,
                "errors": self.errors_count,
                "warnings": self.warnings_count,
            },
            "issues": [
                {
                    "level": i.level.value,
                    "category": i.category,
                    "item": i.item,
                    "message": i.message,
                    "suggestion": i.suggestion,
                }
                for i in self.issues
            ]
        }


class MetadataValidator:
    """
    Validates extracted Tableau metadata for completeness and accuracy.
    
    Checks:
    - Structural integrity
    - Field consistency
    - Calculation validity
    - Relationship integrity
    - Best practices
    """
    
    def __init__(self, strict_mode: bool = False):
        """
        Initialize the validator.
        
        Args:
            strict_mode: If True, treat warnings as errors
        """
        self.strict_mode = strict_mode
    
    def validate(self, metadata: WorkbookMetadata) -> ValidationResult:
        """
        Validate the extracted metadata.
        
        Args:
            metadata: WorkbookMetadata to validate
            
        Returns:
            ValidationResult: Validation results
        """
        result = ValidationResult()
        
        # Structural validation
        self._validate_structure(metadata, result)
        
        # Data source validation
        for ds in metadata.datasources:
            self._validate_datasource(ds, result)
        
        # Sheet validation
        for sheet in metadata.sheets:
            self._validate_sheet(sheet, metadata, result)
        
        # Dashboard validation
        for dashboard in metadata.dashboards:
            self._validate_dashboard(dashboard, metadata, result)
        
        # Relationship validation
        self._validate_relationships(metadata, result)
        
        # Calculate final stats
        result.passed_items = result.checked_items - result.errors_count - result.critical_count
        
        return result
    
    def _validate_structure(self, metadata: WorkbookMetadata, result: ValidationResult):
        """Validate basic structure."""
        result.checked_items += 1
        
        # Check for workbook name
        if not metadata.name:
            result.add_issue(ValidationIssue(
                level=ValidationLevel.ERROR,
                category="structure",
                item="workbook",
                message="Workbook name is missing",
                suggestion="Ensure the .twbx file is valid",
            ))
        
        # Check for at least one data source
        result.checked_items += 1
        if not metadata.datasources:
            result.add_issue(ValidationIssue(
                level=ValidationLevel.WARNING,
                category="structure",
                item="datasources",
                message="No data sources found in workbook",
                suggestion="Verify the workbook has connected data sources",
            ))
        
        # Check for at least one sheet
        result.checked_items += 1
        if not metadata.sheets:
            result.add_issue(ValidationIssue(
                level=ValidationLevel.WARNING,
                category="structure",
                item="sheets",
                message="No worksheets found in workbook",
                suggestion="Verify the workbook has visible worksheets",
            ))
    
    def _validate_datasource(self, ds: DataSourceMetadata, result: ValidationResult):
        """Validate a data source."""
        result.checked_items += 1
        
        # Check for data source name
        if not ds.name:
            result.add_issue(ValidationIssue(
                level=ValidationLevel.ERROR,
                category="datasource",
                item="unknown",
                message="Data source has no name",
            ))
        
        # Check for fields
        result.checked_items += 1
        if not ds.fields and not ds.calculated_fields:
            result.add_issue(ValidationIssue(
                level=ValidationLevel.WARNING,
                category="datasource",
                item=ds.name,
                message=f"Data source '{ds.name}' has no fields",
                suggestion="Verify the data connection is valid",
            ))
        
        # Validate calculated fields
        for calc in ds.calculated_fields:
            self._validate_calculated_field(calc, ds, result)
    
    def _validate_calculated_field(
        self,
        calc: CalculatedFieldMetadata,
        ds: DataSourceMetadata,
        result: ValidationResult
    ):
        """Validate a calculated field."""
        result.checked_items += 1
        
        # Check for formula
        if not calc.formula:
            result.add_issue(ValidationIssue(
                level=ValidationLevel.ERROR,
                category="calculated_field",
                item=calc.name,
                message=f"Calculated field '{calc.name}' has no formula",
            ))
            return
        
        # Check referenced fields exist
        all_field_names = {f.name for f in ds.fields}
        all_field_names.update(c.name for c in ds.calculated_fields)
        
        for ref_field in calc.referenced_fields:
            result.checked_items += 1
            # Skip parameters and special fields
            if ref_field.startswith("Parameter") or ref_field.startswith(":"):
                continue
            
            if ref_field not in all_field_names:
                result.add_issue(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    category="calculated_field",
                    item=calc.name,
                    message=f"Referenced field '{ref_field}' not found in data source",
                    suggestion="Field may have been renamed or removed",
                ))
        
        # Check for complex calculations
        if calc.complexity_score > 70:
            result.add_issue(ValidationIssue(
                level=ValidationLevel.INFO,
                category="calculated_field",
                item=calc.name,
                message=f"Complex calculation detected (complexity: {calc.complexity_score})",
                suggestion="Consider breaking into smaller calculations for maintainability",
            ))
    
    def _validate_sheet(
        self,
        sheet: SheetMetadata,
        metadata: WorkbookMetadata,
        result: ValidationResult
    ):
        """Validate a worksheet."""
        result.checked_items += 1
        
        # Check for sheet name
        if not sheet.name:
            result.add_issue(ValidationIssue(
                level=ValidationLevel.ERROR,
                category="sheet",
                item="unknown",
                message="Sheet has no name",
            ))
            return
        
        # Validate visual configuration
        if sheet.visual:
            self._validate_visual(sheet.visual, sheet.name, result)
        
        # Validate filters
        for filter in sheet.filters:
            self._validate_filter(filter, sheet.name, result)
        
        # Check field usage
        result.checked_items += 1
        if not sheet.all_fields_used:
            result.add_issue(ValidationIssue(
                level=ValidationLevel.INFO,
                category="sheet",
                item=sheet.name,
                message=f"Sheet '{sheet.name}' has no fields on shelves",
                suggestion="Sheet may be blank or using only text/images",
            ))
        
        # Check datasource reference
        result.checked_items += 1
        if sheet.datasource_name:
            ds_names = [ds.name for ds in metadata.datasources]
            if sheet.datasource_name not in ds_names:
                result.add_issue(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    category="sheet",
                    item=sheet.name,
                    message=f"Referenced datasource '{sheet.datasource_name}' not found",
                ))
    
    def _validate_visual(
        self,
        visual: VisualMetadata,
        sheet_name: str,
        result: ValidationResult
    ):
        """Validate visual configuration."""
        result.checked_items += 1
        
        # Check for mark type
        if visual.chart_type.value == "automatic":
            result.add_issue(ValidationIssue(
                level=ValidationLevel.INFO,
                category="visual",
                item=sheet_name,
                message="Chart type is set to Automatic",
                suggestion="Explicit chart type provides more predictable behavior",
            ))
        
        # Check for valid encodings
        result.checked_items += 1
        has_data = bool(visual.rows or visual.columns)
        if not has_data:
            result.add_issue(ValidationIssue(
                level=ValidationLevel.INFO,
                category="visual",
                item=sheet_name,
                message="No fields on rows or columns",
            ))
        
        # Validate axis configuration
        if visual.x_axis:
            result.checked_items += 1
        if visual.y_axis:
            result.checked_items += 1
    
    def _validate_filter(
        self,
        filter: FilterMetadata,
        sheet_name: str,
        result: ValidationResult
    ):
        """Validate a filter."""
        result.checked_items += 1
        
        # Check for field
        if not filter.field:
            result.add_issue(ValidationIssue(
                level=ValidationLevel.ERROR,
                category="filter",
                item=sheet_name,
                message="Filter has no field specified",
            ))
            return
        
        # Check filter values for categorical
        if filter.filter_type.value == "categorical":
            result.checked_items += 1
            if not filter.include_values and not filter.exclude_values:
                result.add_issue(ValidationIssue(
                    level=ValidationLevel.INFO,
                    category="filter",
                    item=f"{sheet_name}/{filter.field}",
                    message=f"Categorical filter on '{filter.field}' has no explicit values",
                    suggestion="May include all values or use show all",
                ))
        
        # Validate range filter
        if filter.filter_type.value == "range":
            result.checked_items += 1
            if filter.range_min is None and filter.range_max is None:
                result.add_issue(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    category="filter",
                    item=f"{sheet_name}/{filter.field}",
                    message=f"Range filter on '{filter.field}' has no min or max",
                ))
    
    def _validate_dashboard(
        self,
        dashboard: DashboardMetadata,
        metadata: WorkbookMetadata,
        result: ValidationResult
    ):
        """Validate a dashboard."""
        result.checked_items += 1
        
        # Check for dashboard name
        if not dashboard.name:
            result.add_issue(ValidationIssue(
                level=ValidationLevel.ERROR,
                category="dashboard",
                item="unknown",
                message="Dashboard has no name",
            ))
            return
        
        # Check for zones
        result.checked_items += 1
        if not dashboard.zones:
            result.add_issue(ValidationIssue(
                level=ValidationLevel.WARNING,
                category="dashboard",
                item=dashboard.name,
                message=f"Dashboard '{dashboard.name}' has no zones",
            ))
        
        # Validate referenced worksheets exist
        sheet_names = {s.name for s in metadata.sheets}
        for ws_name in dashboard.worksheets:
            result.checked_items += 1
            if ws_name not in sheet_names:
                result.add_issue(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    category="dashboard",
                    item=dashboard.name,
                    message=f"Referenced worksheet '{ws_name}' not found",
                ))
        
        # Validate actions
        for action in dashboard.actions:
            result.checked_items += 1
            for source in action.source_worksheets:
                if source not in sheet_names and source not in dashboard.worksheets:
                    result.add_issue(ValidationIssue(
                        level=ValidationLevel.WARNING,
                        category="dashboard_action",
                        item=action.name,
                        message=f"Action source worksheet '{source}' not found",
                    ))
    
    def _validate_relationships(self, metadata: WorkbookMetadata, result: ValidationResult):
        """Validate relationship consistency."""
        result.checked_items += 1
        
        # Check for orphaned calculations
        all_calc_names = set()
        for ds in metadata.datasources:
            for calc in ds.calculated_fields:
                all_calc_names.add(calc.name)
        
        # Verify relationships point to valid entities
        for rel in metadata.relationships:
            result.checked_items += 1
            
            if rel.source_type == "field":
                # Verify field exists
                field_found = False
                for ds in metadata.datasources:
                    if any(f.name == rel.source_name for f in ds.fields):
                        field_found = True
                        break
                    if any(c.name == rel.source_name for c in ds.calculated_fields):
                        field_found = True
                        break
                
                if not field_found:
                    result.add_issue(ValidationIssue(
                        level=ValidationLevel.INFO,
                        category="relationship",
                        item=rel.source_name,
                        message=f"Relationship references unknown field '{rel.source_name}'",
                    ))
    
    def generate_report(self, result: ValidationResult) -> str:
        """Generate a human-readable validation report."""
        lines = [
            "=" * 60,
            "TABLEAU METADATA VALIDATION REPORT",
            "=" * 60,
            "",
            f"Validation Score: {result.get_score()}/100",
            f"Status: {'PASSED' if result.is_valid else 'FAILED'}",
            "",
            "SUMMARY",
            "-" * 40,
            f"Items Checked: {result.checked_items}",
            f"Items Passed: {result.passed_items}",
            f"Critical Issues: {result.critical_count}",
            f"Errors: {result.errors_count}",
            f"Warnings: {result.warnings_count}",
            "",
        ]
        
        # Group issues by level
        if result.issues:
            lines.append("ISSUES")
            lines.append("-" * 40)
            
            for level in [ValidationLevel.CRITICAL, ValidationLevel.ERROR,
                         ValidationLevel.WARNING, ValidationLevel.INFO]:
                level_issues = [i for i in result.issues if i.level == level]
                if level_issues:
                    lines.append(f"\n[{level.value.upper()}]")
                    for issue in level_issues[:15]:
                        lines.append(f"  • {issue.category}/{issue.item}: {issue.message}")
                        if issue.suggestion:
                            lines.append(f"    → Suggestion: {issue.suggestion}")
                    if len(level_issues) > 15:
                        lines.append(f"  ... and {len(level_issues) - 15} more")
        else:
            lines.append("No issues found! ✓")
        
        lines.extend(["", "=" * 60])
        
        return "\n".join(lines)
