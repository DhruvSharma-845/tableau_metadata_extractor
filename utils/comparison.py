"""
Comparison utility to compare metadata from Option A (XML) and Option C (API).

This helps validate accuracy and identify differences between extraction methods.
"""

from typing import List, Dict, Any, Optional, Set, Tuple
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
    ParameterMetadata,
)


class DifferenceType(str, Enum):
    """Types of differences found."""
    MISSING_IN_XML = "missing_in_xml"
    MISSING_IN_API = "missing_in_api"
    VALUE_MISMATCH = "value_mismatch"
    TYPE_MISMATCH = "type_mismatch"
    COUNT_MISMATCH = "count_mismatch"


class DifferenceSeverity(str, Enum):
    """Severity of differences."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Difference:
    """Represents a difference between two metadata extractions."""
    category: str  # e.g., "field", "sheet", "dashboard"
    item_name: str
    difference_type: DifferenceType
    severity: DifferenceSeverity
    description: str
    xml_value: Optional[Any] = None
    api_value: Optional[Any] = None
    path: Optional[str] = None


@dataclass
class ComparisonResult:
    """Result of comparing two metadata extractions."""
    xml_source: str
    api_source: str
    total_differences: int = 0
    critical_differences: int = 0
    error_differences: int = 0
    warning_differences: int = 0
    info_differences: int = 0
    differences: List[Difference] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    
    def add_difference(self, diff: Difference):
        """Add a difference to the result."""
        self.differences.append(diff)
        self.total_differences += 1
        
        if diff.severity == DifferenceSeverity.CRITICAL:
            self.critical_differences += 1
        elif diff.severity == DifferenceSeverity.ERROR:
            self.error_differences += 1
        elif diff.severity == DifferenceSeverity.WARNING:
            self.warning_differences += 1
        else:
            self.info_differences += 1
    
    def get_match_percentage(self) -> float:
        """Calculate overall match percentage."""
        total_items = self.summary.get("total_items_compared", 0)
        if total_items == 0:
            return 100.0
        
        # Weight different severity levels
        weighted_diff = (
            self.critical_differences * 4 +
            self.error_differences * 2 +
            self.warning_differences * 1 +
            self.info_differences * 0.5
        )
        
        match_score = max(0, 100 - (weighted_diff / total_items * 10))
        return round(match_score, 2)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "xml_source": self.xml_source,
            "api_source": self.api_source,
            "match_percentage": self.get_match_percentage(),
            "total_differences": self.total_differences,
            "by_severity": {
                "critical": self.critical_differences,
                "error": self.error_differences,
                "warning": self.warning_differences,
                "info": self.info_differences,
            },
            "summary": self.summary,
            "differences": [
                {
                    "category": d.category,
                    "item_name": d.item_name,
                    "type": d.difference_type.value,
                    "severity": d.severity.value,
                    "description": d.description,
                    "xml_value": str(d.xml_value) if d.xml_value else None,
                    "api_value": str(d.api_value) if d.api_value else None,
                }
                for d in self.differences
            ]
        }


class MetadataComparator:
    """
    Compares metadata extracted via XML (Option A) vs Metadata API (Option C).
    
    This helps validate accuracy and identify which method is more suitable
    for different use cases.
    """
    
    def __init__(self):
        """Initialize the comparator."""
        pass
    
    def compare(
        self,
        xml_metadata: WorkbookMetadata,
        api_metadata: WorkbookMetadata
    ) -> ComparisonResult:
        """
        Compare metadata from XML extraction vs API extraction.
        
        Args:
            xml_metadata: Metadata extracted via XML parsing
            api_metadata: Metadata extracted via Metadata API
            
        Returns:
            ComparisonResult: Detailed comparison result
        """
        result = ComparisonResult(
            xml_source=xml_metadata.source_file or "xml",
            api_source="Tableau Server API",
        )
        
        # Track total items for match percentage
        total_items = 0
        
        # Compare workbook-level info
        if xml_metadata.name != api_metadata.name:
            result.add_difference(Difference(
                category="workbook",
                item_name="name",
                difference_type=DifferenceType.VALUE_MISMATCH,
                severity=DifferenceSeverity.WARNING,
                description="Workbook name mismatch",
                xml_value=xml_metadata.name,
                api_value=api_metadata.name,
            ))
        total_items += 1
        
        # Compare data sources
        ds_diffs, ds_count = self._compare_datasources(
            xml_metadata.datasources,
            api_metadata.datasources
        )
        for diff in ds_diffs:
            result.add_difference(diff)
        total_items += ds_count
        
        # Compare sheets
        sheet_diffs, sheet_count = self._compare_sheets(
            xml_metadata.sheets,
            api_metadata.sheets
        )
        for diff in sheet_diffs:
            result.add_difference(diff)
        total_items += sheet_count
        
        # Compare dashboards
        dash_diffs, dash_count = self._compare_dashboards(
            xml_metadata.dashboards,
            api_metadata.dashboards
        )
        for diff in dash_diffs:
            result.add_difference(diff)
        total_items += dash_count
        
        # Compare parameters
        param_diffs, param_count = self._compare_parameters(
            xml_metadata.parameters,
            api_metadata.parameters
        )
        for diff in param_diffs:
            result.add_difference(diff)
        total_items += param_count
        
        # Build summary
        result.summary = {
            "total_items_compared": total_items,
            "xml_stats": {
                "datasources": len(xml_metadata.datasources),
                "sheets": len(xml_metadata.sheets),
                "dashboards": len(xml_metadata.dashboards),
                "parameters": len(xml_metadata.parameters),
                "total_fields": xml_metadata.total_fields,
                "calculated_fields": xml_metadata.total_calculated_fields,
            },
            "api_stats": {
                "datasources": len(api_metadata.datasources),
                "sheets": len(api_metadata.sheets),
                "dashboards": len(api_metadata.dashboards),
                "parameters": len(api_metadata.parameters),
                "total_fields": api_metadata.total_fields,
                "calculated_fields": api_metadata.total_calculated_fields,
            },
        }
        
        return result
    
    def _compare_datasources(
        self,
        xml_ds: List[DataSourceMetadata],
        api_ds: List[DataSourceMetadata]
    ) -> Tuple[List[Difference], int]:
        """Compare data sources."""
        differences = []
        count = 0
        
        xml_names = {ds.name for ds in xml_ds}
        api_names = {ds.name for ds in api_ds}
        
        # Check for missing datasources
        for name in xml_names - api_names:
            differences.append(Difference(
                category="datasource",
                item_name=name,
                difference_type=DifferenceType.MISSING_IN_API,
                severity=DifferenceSeverity.WARNING,
                description=f"Datasource '{name}' found in XML but not in API",
            ))
        count += len(xml_names - api_names)
        
        for name in api_names - xml_names:
            differences.append(Difference(
                category="datasource",
                item_name=name,
                difference_type=DifferenceType.MISSING_IN_XML,
                severity=DifferenceSeverity.WARNING,
                description=f"Datasource '{name}' found in API but not in XML",
            ))
        count += len(api_names - xml_names)
        
        # Compare common datasources
        for name in xml_names & api_names:
            xml_datasource = next(ds for ds in xml_ds if ds.name == name)
            api_datasource = next(ds for ds in api_ds if ds.name == name)
            
            # Compare fields
            field_diffs, field_count = self._compare_fields(
                xml_datasource.fields,
                api_datasource.fields,
                name
            )
            differences.extend(field_diffs)
            count += field_count
            
            # Compare calculated fields
            calc_diffs, calc_count = self._compare_calculated_fields(
                xml_datasource.calculated_fields,
                api_datasource.calculated_fields,
                name
            )
            differences.extend(calc_diffs)
            count += calc_count
        
        count += len(xml_names & api_names)
        
        return differences, count
    
    def _compare_fields(
        self,
        xml_fields: List[FieldMetadata],
        api_fields: List[FieldMetadata],
        datasource_name: str
    ) -> Tuple[List[Difference], int]:
        """Compare fields in a datasource."""
        differences = []
        
        xml_names = {f.name for f in xml_fields}
        api_names = {f.name for f in api_fields}
        
        for name in xml_names - api_names:
            differences.append(Difference(
                category="field",
                item_name=name,
                difference_type=DifferenceType.MISSING_IN_API,
                severity=DifferenceSeverity.INFO,
                description=f"Field '{name}' in datasource '{datasource_name}' not found in API",
                path=f"datasources/{datasource_name}/fields/{name}",
            ))
        
        for name in api_names - xml_names:
            differences.append(Difference(
                category="field",
                item_name=name,
                difference_type=DifferenceType.MISSING_IN_XML,
                severity=DifferenceSeverity.INFO,
                description=f"Field '{name}' in datasource '{datasource_name}' not found in XML",
                path=f"datasources/{datasource_name}/fields/{name}",
            ))
        
        # Compare common fields
        for name in xml_names & api_names:
            xml_field = next(f for f in xml_fields if f.name == name)
            api_field = next(f for f in api_fields if f.name == name)
            
            if xml_field.data_type != api_field.data_type:
                differences.append(Difference(
                    category="field",
                    item_name=name,
                    difference_type=DifferenceType.TYPE_MISMATCH,
                    severity=DifferenceSeverity.WARNING,
                    description=f"Data type mismatch for field '{name}'",
                    xml_value=xml_field.data_type.value,
                    api_value=api_field.data_type.value,
                    path=f"datasources/{datasource_name}/fields/{name}/data_type",
                ))
            
            if xml_field.role != api_field.role:
                differences.append(Difference(
                    category="field",
                    item_name=name,
                    difference_type=DifferenceType.VALUE_MISMATCH,
                    severity=DifferenceSeverity.INFO,
                    description=f"Role mismatch for field '{name}'",
                    xml_value=xml_field.role.value,
                    api_value=api_field.role.value,
                    path=f"datasources/{datasource_name}/fields/{name}/role",
                ))
        
        return differences, len(xml_names | api_names)
    
    def _compare_calculated_fields(
        self,
        xml_calcs: List[CalculatedFieldMetadata],
        api_calcs: List[CalculatedFieldMetadata],
        datasource_name: str
    ) -> Tuple[List[Difference], int]:
        """Compare calculated fields."""
        differences = []
        
        xml_names = {c.name for c in xml_calcs}
        api_names = {c.name for c in api_calcs}
        
        for name in xml_names - api_names:
            differences.append(Difference(
                category="calculated_field",
                item_name=name,
                difference_type=DifferenceType.MISSING_IN_API,
                severity=DifferenceSeverity.WARNING,
                description=f"Calculated field '{name}' not found in API",
                path=f"datasources/{datasource_name}/calculated_fields/{name}",
            ))
        
        for name in api_names - xml_names:
            differences.append(Difference(
                category="calculated_field",
                item_name=name,
                difference_type=DifferenceType.MISSING_IN_XML,
                severity=DifferenceSeverity.WARNING,
                description=f"Calculated field '{name}' not found in XML",
                path=f"datasources/{datasource_name}/calculated_fields/{name}",
            ))
        
        # Compare formulas
        for name in xml_names & api_names:
            xml_calc = next(c for c in xml_calcs if c.name == name)
            api_calc = next(c for c in api_calcs if c.name == name)
            
            # Normalize formulas for comparison
            xml_formula = self._normalize_formula(xml_calc.formula)
            api_formula = self._normalize_formula(api_calc.formula)
            
            if xml_formula != api_formula:
                differences.append(Difference(
                    category="calculated_field",
                    item_name=name,
                    difference_type=DifferenceType.VALUE_MISMATCH,
                    severity=DifferenceSeverity.ERROR,
                    description=f"Formula mismatch for calculated field '{name}'",
                    xml_value=xml_calc.formula[:100],
                    api_value=api_calc.formula[:100] if api_calc.formula else None,
                    path=f"datasources/{datasource_name}/calculated_fields/{name}/formula",
                ))
        
        return differences, len(xml_names | api_names)
    
    def _normalize_formula(self, formula: str) -> str:
        """Normalize a formula for comparison."""
        if not formula:
            return ""
        
        # Remove extra whitespace
        normalized = " ".join(formula.split())
        
        # Remove datasource prefixes
        import re
        normalized = re.sub(r'\[federated\.[^\]]+\]\.', '', normalized)
        
        return normalized.lower()
    
    def _compare_sheets(
        self,
        xml_sheets: List[SheetMetadata],
        api_sheets: List[SheetMetadata]
    ) -> Tuple[List[Difference], int]:
        """Compare sheets."""
        differences = []
        
        xml_names = {s.name for s in xml_sheets}
        api_names = {s.name for s in api_sheets}
        
        for name in xml_names - api_names:
            differences.append(Difference(
                category="sheet",
                item_name=name,
                difference_type=DifferenceType.MISSING_IN_API,
                severity=DifferenceSeverity.WARNING,
                description=f"Sheet '{name}' found in XML but not in API",
            ))
        
        for name in api_names - xml_names:
            differences.append(Difference(
                category="sheet",
                item_name=name,
                difference_type=DifferenceType.MISSING_IN_XML,
                severity=DifferenceSeverity.WARNING,
                description=f"Sheet '{name}' found in API but not in XML",
            ))
        
        # Compare fields used in common sheets
        for name in xml_names & api_names:
            xml_sheet = next(s for s in xml_sheets if s.name == name)
            api_sheet = next(s for s in api_sheets if s.name == name)
            
            xml_fields = set(xml_sheet.all_fields_used)
            api_fields = set(api_sheet.all_fields_used)
            
            if xml_fields != api_fields:
                missing_in_api = xml_fields - api_fields
                missing_in_xml = api_fields - xml_fields
                
                if missing_in_api:
                    differences.append(Difference(
                        category="sheet_field",
                        item_name=name,
                        difference_type=DifferenceType.MISSING_IN_API,
                        severity=DifferenceSeverity.INFO,
                        description=f"Fields in sheet '{name}' not found in API: {missing_in_api}",
                        xml_value=list(missing_in_api),
                    ))
                
                if missing_in_xml:
                    differences.append(Difference(
                        category="sheet_field",
                        item_name=name,
                        difference_type=DifferenceType.MISSING_IN_XML,
                        severity=DifferenceSeverity.INFO,
                        description=f"Fields in sheet '{name}' not found in XML: {missing_in_xml}",
                        api_value=list(missing_in_xml),
                    ))
        
        return differences, len(xml_names | api_names)
    
    def _compare_dashboards(
        self,
        xml_dashboards: List[DashboardMetadata],
        api_dashboards: List[DashboardMetadata]
    ) -> Tuple[List[Difference], int]:
        """Compare dashboards."""
        differences = []
        
        xml_names = {d.name for d in xml_dashboards}
        api_names = {d.name for d in api_dashboards}
        
        for name in xml_names - api_names:
            differences.append(Difference(
                category="dashboard",
                item_name=name,
                difference_type=DifferenceType.MISSING_IN_API,
                severity=DifferenceSeverity.WARNING,
                description=f"Dashboard '{name}' found in XML but not in API",
            ))
        
        for name in api_names - xml_names:
            differences.append(Difference(
                category="dashboard",
                item_name=name,
                difference_type=DifferenceType.MISSING_IN_XML,
                severity=DifferenceSeverity.WARNING,
                description=f"Dashboard '{name}' found in API but not in XML",
            ))
        
        # Compare worksheets in common dashboards
        for name in xml_names & api_names:
            xml_dash = next(d for d in xml_dashboards if d.name == name)
            api_dash = next(d for d in api_dashboards if d.name == name)
            
            xml_ws = set(xml_dash.worksheets)
            api_ws = set(api_dash.worksheets)
            
            if xml_ws != api_ws:
                differences.append(Difference(
                    category="dashboard",
                    item_name=name,
                    difference_type=DifferenceType.VALUE_MISMATCH,
                    severity=DifferenceSeverity.WARNING,
                    description=f"Worksheet list mismatch in dashboard '{name}'",
                    xml_value=list(xml_ws),
                    api_value=list(api_ws),
                ))
        
        return differences, len(xml_names | api_names)
    
    def _compare_parameters(
        self,
        xml_params: List[ParameterMetadata],
        api_params: List[ParameterMetadata]
    ) -> Tuple[List[Difference], int]:
        """Compare parameters."""
        differences = []
        
        xml_names = {p.name for p in xml_params}
        api_names = {p.name for p in api_params}
        
        for name in xml_names - api_names:
            differences.append(Difference(
                category="parameter",
                item_name=name,
                difference_type=DifferenceType.MISSING_IN_API,
                severity=DifferenceSeverity.WARNING,
                description=f"Parameter '{name}' found in XML but not in API",
            ))
        
        for name in api_names - xml_names:
            differences.append(Difference(
                category="parameter",
                item_name=name,
                difference_type=DifferenceType.MISSING_IN_XML,
                severity=DifferenceSeverity.WARNING,
                description=f"Parameter '{name}' found in API but not in XML",
            ))
        
        return differences, len(xml_names | api_names)
    
    def generate_report(self, result: ComparisonResult) -> str:
        """Generate a human-readable comparison report."""
        lines = [
            "=" * 60,
            "TABLEAU METADATA COMPARISON REPORT",
            "=" * 60,
            "",
            f"XML Source: {result.xml_source}",
            f"API Source: {result.api_source}",
            "",
            f"Match Percentage: {result.get_match_percentage()}%",
            "",
            "SUMMARY",
            "-" * 40,
            f"Total Differences: {result.total_differences}",
            f"  Critical: {result.critical_differences}",
            f"  Errors: {result.error_differences}",
            f"  Warnings: {result.warning_differences}",
            f"  Info: {result.info_differences}",
            "",
        ]
        
        # Add stats comparison
        if result.summary:
            lines.extend([
                "EXTRACTION COMPARISON",
                "-" * 40,
            ])
            
            xml_stats = result.summary.get("xml_stats", {})
            api_stats = result.summary.get("api_stats", {})
            
            for key in xml_stats:
                xml_val = xml_stats.get(key, 0)
                api_val = api_stats.get(key, 0)
                match_indicator = "✓" if xml_val == api_val else "✗"
                lines.append(f"  {key}: XML={xml_val}, API={api_val} {match_indicator}")
            
            lines.append("")
        
        # List differences by severity
        if result.differences:
            lines.extend([
                "DIFFERENCES",
                "-" * 40,
            ])
            
            for severity in [DifferenceSeverity.CRITICAL, DifferenceSeverity.ERROR, 
                           DifferenceSeverity.WARNING, DifferenceSeverity.INFO]:
                severity_diffs = [d for d in result.differences if d.severity == severity]
                if severity_diffs:
                    lines.append(f"\n[{severity.value.upper()}]")
                    for diff in severity_diffs[:10]:  # Limit output
                        lines.append(f"  - {diff.category}/{diff.item_name}: {diff.description}")
                    if len(severity_diffs) > 10:
                        lines.append(f"  ... and {len(severity_diffs) - 10} more")
        
        lines.extend(["", "=" * 60])
        
        return "\n".join(lines)
