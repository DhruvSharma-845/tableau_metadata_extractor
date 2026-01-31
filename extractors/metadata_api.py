"""
Option C: Tableau Metadata API client for Tableau Server/Online.

This module connects to published workbooks on Tableau Server/Online
using the Metadata API (GraphQL) to extract metadata.

Note: This requires a published workbook and authentication credentials.
For local .twbx files, use the XMLMetadataExtractor (Option A).
"""

import json
from typing import Optional, List, Dict, Any
from datetime import datetime

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from models.metadata_models import (
    DataType,
    AggregationType,
    CalculationType,
    FilterType,
    FieldRole,
    FieldMetadata,
    CalculatedFieldMetadata,
    FilterMetadata,
    SheetMetadata,
    DashboardMetadata,
    DataSourceMetadata,
    ParameterMetadata,
    RelationshipMetadata,
    WorkbookMetadata,
)


class TableauMetadataAPIClient:
    """
    Client for Tableau Metadata API (GraphQL).
    
    Extracts metadata from published workbooks on Tableau Server/Online.
    Requires personal access token or session authentication.
    """
    
    # GraphQL endpoint path
    METADATA_API_PATH = "/api/metadata/graphql"
    
    # REST API paths for auth
    SIGNIN_PATH = "/api/3.21/auth/signin"
    
    def __init__(
        self,
        server_url: str,
        site_id: str = "",
        token_name: Optional[str] = None,
        token_secret: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        api_version: str = "3.21"
    ):
        """
        Initialize the Metadata API client.
        
        Args:
            server_url: Tableau Server URL (e.g., https://tableau.company.com)
            site_id: Site content URL (empty string for default site)
            token_name: Personal access token name (preferred)
            token_secret: Personal access token secret
            username: Username for basic auth (alternative)
            password: Password for basic auth (alternative)
            api_version: REST API version
        """
        self.server_url = server_url.rstrip("/")
        self.site_id = site_id
        self.token_name = token_name
        self.token_secret = token_secret
        self.username = username
        self.password = password
        self.api_version = api_version
        
        self.auth_token: Optional[str] = None
        self.site_luid: Optional[str] = None
        
        # Session with retry
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic."""
        session = requests.Session()
        
        retries = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def authenticate(self) -> bool:
        """
        Authenticate with Tableau Server.
        
        Returns:
            bool: True if authentication successful
        """
        signin_url = f"{self.server_url}/api/{self.api_version}/auth/signin"
        
        if self.token_name and self.token_secret:
            # Personal Access Token auth
            payload = {
                "credentials": {
                    "personalAccessTokenName": self.token_name,
                    "personalAccessTokenSecret": self.token_secret,
                    "site": {"contentUrl": self.site_id}
                }
            }
        elif self.username and self.password:
            # Username/password auth
            payload = {
                "credentials": {
                    "name": self.username,
                    "password": self.password,
                    "site": {"contentUrl": self.site_id}
                }
            }
        else:
            raise ValueError("Must provide either token or username/password credentials")
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        response = self.session.post(signin_url, json=payload, headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"Authentication failed: {response.status_code} - {response.text}")
        
        data = response.json()
        self.auth_token = data["credentials"]["token"]
        self.site_luid = data["credentials"]["site"]["id"]
        
        return True
    
    def _graphql_query(self, query: str, variables: Optional[Dict] = None) -> Dict:
        """
        Execute a GraphQL query against the Metadata API.
        
        Args:
            query: GraphQL query string
            variables: Optional query variables
            
        Returns:
            Dict: Query response data
        """
        if not self.auth_token:
            self.authenticate()
        
        url = f"{self.server_url}{self.METADATA_API_PATH}"
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Tableau-Auth": self.auth_token
        }
        
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        response = self.session.post(url, json=payload, headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"GraphQL query failed: {response.status_code} - {response.text}")
        
        result = response.json()
        
        if "errors" in result:
            raise Exception(f"GraphQL errors: {result['errors']}")
        
        return result.get("data", {})
    
    def get_workbook_metadata(
        self,
        workbook_name: str,
        project_name: Optional[str] = None
    ) -> WorkbookMetadata:
        """
        Get complete metadata for a workbook.
        
        Args:
            workbook_name: Name of the workbook
            project_name: Optional project name to filter
            
        Returns:
            WorkbookMetadata: Complete metadata object
        """
        # Get basic workbook info
        workbook_data = self._query_workbook(workbook_name, project_name)
        
        if not workbook_data:
            raise ValueError(f"Workbook '{workbook_name}' not found")
        
        workbook_luid = workbook_data.get("luid")
        
        # Get detailed metadata
        sheets_data = self._query_sheets(workbook_luid)
        datasources_data = self._query_datasources(workbook_luid)
        dashboards_data = self._query_dashboards(workbook_luid)
        
        # Build metadata objects
        datasources = self._build_datasources(datasources_data)
        sheets = self._build_sheets(sheets_data)
        dashboards = self._build_dashboards(dashboards_data)
        parameters = self._extract_parameters(datasources_data)
        
        # Build relationships
        relationships = self._build_relationships_from_api(
            workbook_data, sheets_data, datasources_data, dashboards_data
        )
        
        metadata = WorkbookMetadata(
            name=workbook_data.get("name", workbook_name),
            version=None,  # Not available via API
            source_file=None,
            extraction_timestamp=datetime.now(),
            extraction_method="api",
            datasources=datasources,
            sheets=sheets,
            dashboards=dashboards,
            parameters=parameters,
            relationships=relationships,
        )
        
        metadata.compute_statistics()
        
        return metadata
    
    def _query_workbook(self, name: str, project_name: Optional[str] = None) -> Optional[Dict]:
        """Query workbook by name."""
        query = """
        query GetWorkbook($name: String!) {
            workbooks(filter: {name: $name}) {
                luid
                name
                projectName
                createdAt
                updatedAt
                owner {
                    name
                }
            }
        }
        """
        
        data = self._graphql_query(query, {"name": name})
        workbooks = data.get("workbooks", [])
        
        if project_name:
            workbooks = [w for w in workbooks if w.get("projectName") == project_name]
        
        return workbooks[0] if workbooks else None
    
    def _query_sheets(self, workbook_luid: str) -> List[Dict]:
        """Query all sheets in a workbook."""
        query = """
        query GetSheets($workbookLuid: String!) {
            sheets(filter: {workbook: {luid: $workbookLuid}}) {
                name
                sheetType
                containedInDashboards {
                    name
                }
                sheetFieldInstances {
                    name
                    datasourceField {
                        name
                        dataType
                        role
                        isCalculated
                        formula
                        aggregation
                    }
                }
            }
        }
        """
        
        data = self._graphql_query(query, {"workbookLuid": workbook_luid})
        return data.get("sheets", [])
    
    def _query_datasources(self, workbook_luid: str) -> List[Dict]:
        """Query all data sources in a workbook."""
        query = """
        query GetDatasources($workbookLuid: String!) {
            embeddedDatasources(filter: {workbook: {luid: $workbookLuid}}) {
                name
                hasExtracts
                extractLastUpdateTime
                fields {
                    name
                    dataType
                    role
                    isCalculated
                    formula
                    aggregation
                    description
                    isHidden
                    referencedByCalculations {
                        name
                    }
                    upstreamColumns {
                        name
                        table {
                            name
                        }
                    }
                }
                upstreamTables {
                    name
                    fullName
                    connectionType
                    database {
                        name
                        connectionType
                    }
                }
            }
        }
        """
        
        data = self._graphql_query(query, {"workbookLuid": workbook_luid})
        return data.get("embeddedDatasources", [])
    
    def _query_dashboards(self, workbook_luid: str) -> List[Dict]:
        """Query all dashboards in a workbook."""
        query = """
        query GetDashboards($workbookLuid: String!) {
            dashboards(filter: {workbook: {luid: $workbookLuid}}) {
                name
                containsSheets {
                    name
                }
            }
        }
        """
        
        data = self._graphql_query(query, {"workbookLuid": workbook_luid})
        return data.get("dashboards", [])
    
    def _map_data_type(self, api_type: str) -> DataType:
        """Map API data type to our enum."""
        type_map = {
            "STRING": DataType.STRING,
            "INTEGER": DataType.INTEGER,
            "REAL": DataType.REAL,
            "BOOLEAN": DataType.BOOLEAN,
            "DATE": DataType.DATE,
            "DATETIME": DataType.DATETIME,
            "SPATIAL": DataType.SPATIAL,
        }
        return type_map.get(api_type, DataType.UNKNOWN)
    
    def _map_aggregation(self, api_agg: str) -> AggregationType:
        """Map API aggregation to our enum."""
        agg_map = {
            "SUM": AggregationType.SUM,
            "AVG": AggregationType.AVG,
            "COUNT": AggregationType.COUNT,
            "COUNTD": AggregationType.COUNTD,
            "MIN": AggregationType.MIN,
            "MAX": AggregationType.MAX,
            "MEDIAN": AggregationType.MEDIAN,
            "ATTR": AggregationType.ATTR,
        }
        return agg_map.get(api_agg, AggregationType.NONE)
    
    def _build_datasources(self, datasources_data: List[Dict]) -> List[DataSourceMetadata]:
        """Build DataSourceMetadata objects from API data."""
        datasources = []
        
        for ds_data in datasources_data:
            fields = []
            calculated_fields = []
            
            for field_data in ds_data.get("fields", []):
                is_calc = field_data.get("isCalculated", False)
                
                if is_calc:
                    calc = CalculatedFieldMetadata(
                        name=field_data.get("name", ""),
                        formula=field_data.get("formula", ""),
                        data_type=self._map_data_type(field_data.get("dataType", "")),
                        role=FieldRole.MEASURE if field_data.get("role") == "MEASURE" else FieldRole.DIMENSION,
                        calculation_type=CalculationType.SIMPLE,  # Would need formula analysis
                    )
                    calculated_fields.append(calc)
                else:
                    field = FieldMetadata(
                        name=field_data.get("name", ""),
                        data_type=self._map_data_type(field_data.get("dataType", "")),
                        role=FieldRole.MEASURE if field_data.get("role") == "MEASURE" else FieldRole.DIMENSION,
                        default_aggregation=self._map_aggregation(field_data.get("aggregation", "")),
                        is_hidden=field_data.get("isHidden", False),
                    )
                    fields.append(field)
            
            # Extract table info
            tables = []
            for table_data in ds_data.get("upstreamTables", []):
                tables.append({
                    "name": table_data.get("name", ""),
                    "full_name": table_data.get("fullName", ""),
                    "connection_type": table_data.get("connectionType", ""),
                    "database": table_data.get("database", {}).get("name") if table_data.get("database") else None,
                })
            
            ds = DataSourceMetadata(
                name=ds_data.get("name", ""),
                has_extract=ds_data.get("hasExtracts", False),
                fields=fields,
                calculated_fields=calculated_fields,
                tables=tables,
            )
            datasources.append(ds)
        
        return datasources
    
    def _build_sheets(self, sheets_data: List[Dict]) -> List[SheetMetadata]:
        """Build SheetMetadata objects from API data."""
        sheets = []
        
        for sheet_data in sheets_data:
            # Skip dashboards
            if sheet_data.get("sheetType") == "dashboard":
                continue
            
            fields_used = []
            for field_inst in sheet_data.get("sheetFieldInstances", []):
                field_name = field_inst.get("name", "")
                if field_name:
                    fields_used.append(field_name)
            
            dashboards = [d.get("name") for d in sheet_data.get("containedInDashboards", [])]
            
            sheet = SheetMetadata(
                name=sheet_data.get("name", ""),
                all_fields_used=fields_used,
                used_in_dashboards=dashboards,
            )
            sheets.append(sheet)
        
        return sheets
    
    def _build_dashboards(self, dashboards_data: List[Dict]) -> List[DashboardMetadata]:
        """Build DashboardMetadata objects from API data."""
        dashboards = []
        
        for dash_data in dashboards_data:
            worksheets = [s.get("name") for s in dash_data.get("containsSheets", [])]
            
            dashboard = DashboardMetadata(
                name=dash_data.get("name", ""),
                worksheets=worksheets,
            )
            dashboards.append(dashboard)
        
        return dashboards
    
    def _extract_parameters(self, datasources_data: List[Dict]) -> List[ParameterMetadata]:
        """Extract parameters from datasource fields."""
        parameters = []
        
        for ds_data in datasources_data:
            for field_data in ds_data.get("fields", []):
                # Parameters typically have specific naming patterns
                name = field_data.get("name", "")
                if name.startswith("Parameter ") or "[Parameters]" in name:
                    param = ParameterMetadata(
                        name=name.replace("Parameter ", "").strip("[]"),
                        data_type=self._map_data_type(field_data.get("dataType", "")),
                    )
                    parameters.append(param)
        
        return parameters
    
    def _build_relationships_from_api(
        self,
        workbook_data: Dict,
        sheets_data: List[Dict],
        datasources_data: List[Dict],
        dashboards_data: List[Dict]
    ) -> List[RelationshipMetadata]:
        """Build relationship metadata from API data."""
        relationships = []
        
        # Sheet to dashboard relationships
        for sheet_data in sheets_data:
            sheet_name = sheet_data.get("name", "")
            for dash in sheet_data.get("containedInDashboards", []):
                relationships.append(RelationshipMetadata(
                    relationship_type="sheet_to_dashboard",
                    source_type="sheet",
                    source_name=sheet_name,
                    target_type="dashboard",
                    target_name=dash.get("name", ""),
                ))
        
        # Field dependencies from calculated fields
        for ds_data in datasources_data:
            for field_data in ds_data.get("fields", []):
                if field_data.get("isCalculated"):
                    field_name = field_data.get("name", "")
                    for ref in field_data.get("referencedByCalculations", []):
                        relationships.append(RelationshipMetadata(
                            relationship_type="calc_to_field",
                            source_type="calculated_field",
                            source_name=ref.get("name", ""),
                            target_type="field",
                            target_name=field_name,
                        ))
        
        return relationships
    
    def list_workbooks(self, project_name: Optional[str] = None) -> List[Dict]:
        """
        List all accessible workbooks.
        
        Args:
            project_name: Optional project filter
            
        Returns:
            List of workbook info dicts
        """
        query = """
        query ListWorkbooks {
            workbooks {
                luid
                name
                projectName
                createdAt
                owner {
                    name
                }
            }
        }
        """
        
        data = self._graphql_query(query)
        workbooks = data.get("workbooks", [])
        
        if project_name:
            workbooks = [w for w in workbooks if w.get("projectName") == project_name]
        
        return workbooks
    
    def close(self):
        """Close the session."""
        if self.session:
            self.session.close()


class MetadataAPINotAvailableError(Exception):
    """Raised when trying to use Metadata API on local files."""
    pass
