"""
Data Quality Monitoring Utilities

This module provides utilities for monitoring and validating data quality
in the streaming analytics pipeline.
"""

import os
import time
import json
import yaml
import logging
import datetime
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataQualityCheck:
    """Base class for data quality checks."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.passed = False
        self.message = ""
        self.timestamp = None
    
    def run(self, data: Any) -> bool:
        """Run the data quality check on the provided data."""
        raise NotImplementedError("Subclasses must implement this method")
    
    def get_result(self) -> Dict[str, Any]:
        """Get the result of the data quality check."""
        return {
            "name": self.name,
            "description": self.description,
            "passed": self.passed,
            "message": self.message,
            "timestamp": self.timestamp,
        }


class NullCheck(DataQualityCheck):
    """Check for null values in specified columns."""
    
    def __init__(self, name: str, columns: List[str], threshold: float = 0.0):
        """
        Initialize the null check.
        
        Args:
            name: Name of the check
            columns: List of columns to check for null values
            threshold: Maximum allowed percentage of null values (0.0 to 1.0)
        """
        super().__init__(name, f"Check for null values in columns: {', '.join(columns)}")
        self.columns = columns
        self.threshold = threshold
    
    def run(self, data: pd.DataFrame) -> bool:
        """
        Run the null check on the provided data.
        
        Args:
            data: Pandas DataFrame to check
            
        Returns:
            bool: True if the check passed, False otherwise
        """
        self.timestamp = datetime.datetime.now()
        
        # Check if all specified columns exist in the data
        missing_columns = [col for col in self.columns if col not in data.columns]
        if missing_columns:
            self.passed = False
            self.message = f"Columns not found in data: {', '.join(missing_columns)}"
            return False
        
        # Calculate the percentage of null values for each column
        null_percentages = {}
        for col in self.columns:
            null_count = data[col].isnull().sum()
            total_count = len(data)
            null_percentage = null_count / total_count if total_count > 0 else 0.0
            null_percentages[col] = null_percentage
        
        # Check if any column exceeds the threshold
        failing_columns = {col: pct for col, pct in null_percentages.items() if pct > self.threshold}
        
        if failing_columns:
            self.passed = False
            self.message = f"Columns with too many null values: {failing_columns}"
            return False
        else:
            self.passed = True
            self.message = "All columns have acceptable null value percentages"
            return True


class ValueRangeCheck(DataQualityCheck):
    """Check if values in specified columns are within expected ranges."""
    
    def __init__(self, name: str, column_ranges: Dict[str, Tuple[Union[int, float], Union[int, float]]]):
        """
        Initialize the value range check.
        
        Args:
            name: Name of the check
            column_ranges: Dictionary mapping column names to (min, max) tuples
        """
        super().__init__(name, f"Check if values are within expected ranges for columns: {', '.join(column_ranges.keys())}")
        self.column_ranges = column_ranges
    
    def run(self, data: pd.DataFrame) -> bool:
        """
        Run the value range check on the provided data.
        
        Args:
            data: Pandas DataFrame to check
            
        Returns:
            bool: True if the check passed, False otherwise
        """
        self.timestamp = datetime.datetime.now()
        
        # Check if all specified columns exist in the data
        missing_columns = [col for col in self.column_ranges.keys() if col not in data.columns]
        if missing_columns:
            self.passed = False
            self.message = f"Columns not found in data: {', '.join(missing_columns)}"
            return False
        
        # Check if values are within the expected range for each column
        out_of_range = {}
        for col, (min_val, max_val) in self.column_ranges.items():
            # Filter out null values before checking the range
            valid_data = data[col].dropna()
            
            # Count values outside the expected range
            below_min = (valid_data < min_val).sum()
            above_max = (valid_data > max_val).sum()
            total_out_of_range = below_min + above_max
            
            if total_out_of_range > 0:
                percentage = total_out_of_range / len(valid_data) if len(valid_data) > 0 else 0.0
                out_of_range[col] = {
                    "below_min": int(below_min),
                    "above_max": int(above_max),
                    "total": int(total_out_of_range),
                    "percentage": float(percentage)
                }
        
        if out_of_range:
            self.passed = False
            self.message = f"Columns with values outside expected ranges: {json.dumps(out_of_range)}"
            return False
        else:
            self.passed = True
            self.message = "All values are within expected ranges"
            return True


class UniquenessCheck(DataQualityCheck):
    """Check if values in specified columns are unique."""
    
    def __init__(self, name: str, columns: List[str], should_be_unique: bool = True):
        """
        Initialize the uniqueness check.
        
        Args:
            name: Name of the check
            columns: List of columns to check for uniqueness
            should_be_unique: Whether the values should be unique (True) or not unique (False)
        """
        super().__init__(
            name, 
            f"Check if values are {'unique' if should_be_unique else 'not unique'} in columns: {', '.join(columns)}"
        )
        self.columns = columns
        self.should_be_unique = should_be_unique
    
    def run(self, data: pd.DataFrame) -> bool:
        """
        Run the uniqueness check on the provided data.
        
        Args:
            data: Pandas DataFrame to check
            
        Returns:
            bool: True if the check passed, False otherwise
        """
        self.timestamp = datetime.datetime.now()
        
        # Check if all specified columns exist in the data
        missing_columns = [col for col in self.columns if col not in data.columns]
        if missing_columns:
            self.passed = False
            self.message = f"Columns not found in data: {', '.join(missing_columns)}"
            return False
        
        # Check uniqueness for each column
        non_unique_columns = {}
        for col in self.columns:
            # Count duplicates
            duplicate_count = data[col].duplicated().sum()
            
            # Check if the result matches the expected uniqueness
            if self.should_be_unique and duplicate_count > 0:
                non_unique_columns[col] = int(duplicate_count)
            elif not self.should_be_unique and duplicate_count == 0:
                non_unique_columns[col] = 0
        
        if non_unique_columns:
            self.passed = False
            if self.should_be_unique:
                self.message = f"Columns with duplicate values: {non_unique_columns}"
            else:
                self.message = f"Columns with no duplicate values: {list(non_unique_columns.keys())}"
            return False
        else:
            self.passed = True
            if self.should_be_unique:
                self.message = "All columns have unique values"
            else:
                self.message = "All columns have duplicate values as expected"
            return True


class SchemaCheck(DataQualityCheck):
    """Check if the data schema matches the expected schema."""
    
    def __init__(self, name: str, expected_schema: Dict[str, str]):
        """
        Initialize the schema check.
        
        Args:
            name: Name of the check
            expected_schema: Dictionary mapping column names to expected data types
        """
        super().__init__(name, "Check if the data schema matches the expected schema")
        self.expected_schema = expected_schema
    
    def run(self, data: pd.DataFrame) -> bool:
        """
        Run the schema check on the provided data.
        
        Args:
            data: Pandas DataFrame to check
            
        Returns:
            bool: True if the check passed, False otherwise
        """
        self.timestamp = datetime.datetime.now()
        
        # Get the actual schema
        actual_schema = {col: str(data[col].dtype) for col in data.columns}
        
        # Check for missing and extra columns
        expected_columns = set(self.expected_schema.keys())
        actual_columns = set(actual_schema.keys())
        
        missing_columns = expected_columns - actual_columns
        extra_columns = actual_columns - expected_columns
        
        # Check for columns with mismatched data types
        mismatched_types = {}
        for col in expected_columns.intersection(actual_columns):
            expected_type = self.expected_schema[col]
            actual_type = actual_schema[col]
            
            # Compare types (allowing for some flexibility in the comparison)
            if expected_type not in actual_type and actual_type not in expected_type:
                mismatched_types[col] = {"expected": expected_type, "actual": actual_type}
        
        if missing_columns or extra_columns or mismatched_types:
            self.passed = False
            self.message = {
                "missing_columns": list(missing_columns),
                "extra_columns": list(extra_columns),
                "mismatched_types": mismatched_types
            }
            return False
        else:
            self.passed = True
            self.message = "Data schema matches the expected schema"
            return True


class AnomalyCheck(DataQualityCheck):
    """Check for anomalies in the data using simple statistical methods."""
    
    def __init__(self, name: str, column: str, method: str = "zscore", threshold: float = 3.0):
        """
        Initialize the anomaly check.
        
        Args:
            name: Name of the check
            column: Column to check for anomalies
            method: Method to use for anomaly detection ('zscore' or 'iqr')
            threshold: Threshold for anomaly detection
        """
        super().__init__(name, f"Check for anomalies in column: {column} using {method} method")
        self.column = column
        self.method = method
        self.threshold = threshold
    
    def run(self, data: pd.DataFrame) -> bool:
        """
        Run the anomaly check on the provided data.
        
        Args:
            data: Pandas DataFrame to check
            
        Returns:
            bool: True if the check passed, False otherwise
        """
        self.timestamp = datetime.datetime.now()
        
        # Check if the specified column exists in the data
        if self.column not in data.columns:
            self.passed = False
            self.message = f"Column not found in data: {self.column}"
            return False
        
        # Get the numeric values from the column
        values = pd.to_numeric(data[self.column], errors='coerce').dropna()
        
        if len(values) == 0:
            self.passed = False
            self.message = f"No valid numeric values in column: {self.column}"
            return False
        
        # Detect anomalies using the specified method
        anomalies = []
        
        if self.method == "zscore":
            # Z-score method
            mean = values.mean()
            std = values.std()
            
            if std == 0:
                self.passed = True
                self.message = f"No variation in column: {self.column}, all values are the same"
                return True
            
            zscores = np.abs((values - mean) / std)
            anomalies = values[zscores > self.threshold].tolist()
            
        elif self.method == "iqr":
            # IQR method
            q1 = values.quantile(0.25)
            q3 = values.quantile(0.75)
            iqr = q3 - q1
            
            lower_bound = q1 - self.threshold * iqr
            upper_bound = q3 + self.threshold * iqr
            
            anomalies = values[(values < lower_bound) | (values > upper_bound)].tolist()
        
        if anomalies:
            self.passed = False
            self.message = f"Found {len(anomalies)} anomalies in column: {self.column}"
            return False
        else:
            self.passed = True
            self.message = f"No anomalies found in column: {self.column}"
            return True


class DataQualityChecker:
    """Class to run multiple data quality checks on a dataset."""
    
    def __init__(self):
        self.checks = []
        self.results = []
    
    def add_check(self, check: DataQualityCheck) -> None:
        """Add a data quality check to the checker."""
        self.checks.append(check)
    
    def run_checks(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Run all data quality checks on the provided data.
        
        Args:
            data: Pandas DataFrame to check
            
        Returns:
            Dict[str, Any]: Results of all checks
        """
        self.results = []
        
        for check in self.checks:
            try:
                check.run(data)
                self.results.append(check.get_result())
            except Exception as e:
                logger.error(f"Error running check {check.name}: {e}")
                # Record the error in the results
                self.results.append({
                    "name": check.name,
                    "description": check.description,
                    "passed": False,
                    "message": f"Error: {str(e)}",
                    "timestamp": datetime.datetime.now(),
                })
        
        return self.get_summary()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all check results."""
        total_checks = len(self.results)
        passed_checks = sum(1 for result in self.results if result["passed"])
        
        return {
            "summary": {
                "total_checks": total_checks,
                "passed_checks": passed_checks,
                "failed_checks": total_checks - passed_checks,
                "pass_rate": passed_checks / total_checks if total_checks > 0 else 0.0,
                "timestamp": datetime.datetime.now(),
            },
            "results": self.results
        }


def load_checks_from_config(config_path: str) -> List[DataQualityCheck]:
    """
    Load data quality checks from a configuration file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        List[DataQualityCheck]: List of data quality checks
    """
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    checks = []
    
    for check_config in config.get("checks", []):
        check_type = check_config.get("type")
        
        if check_type == "null_check":
            check = NullCheck(
                name=check_config.get("name"),
                columns=check_config.get("columns", []),
                threshold=check_config.get("threshold", 0.0)
            )
            checks.append(check)
            
        elif check_type == "value_range_check":
            column_ranges = {}
            for col_range in check_config.get("column_ranges", []):
                column_ranges[col_range["column"]] = (col_range["min"], col_range["max"])
            
            check = ValueRangeCheck(
                name=check_config.get("name"),
                column_ranges=column_ranges
            )
            checks.append(check)
            
        elif check_type == "uniqueness_check":
            check = UniquenessCheck(
                name=check_config.get("name"),
                columns=check_config.get("columns", []),
                should_be_unique=check_config.get("should_be_unique", True)
            )
            checks.append(check)
            
        elif check_type == "schema_check":
            check = SchemaCheck(
                name=check_config.get("name"),
                expected_schema=check_config.get("expected_schema", {})
            )
            checks.append(check)
            
        elif check_type == "anomaly_check":
            check = AnomalyCheck(
                name=check_config.get("name"),
                column=check_config.get("column"),
                method=check_config.get("method", "zscore"),
                threshold=check_config.get("threshold", 3.0)
            )
            checks.append(check)
    
    return checks


def run_quality_checks_on_dataframe(df: pd.DataFrame, checks: List[DataQualityCheck]) -> Dict[str, Any]:
    """
    Run data quality checks on a DataFrame.
    
    Args:
        df: Pandas DataFrame to check
        checks: List of data quality checks to run
        
    Returns:
        Dict[str, Any]: Results of all checks
    """
    checker = DataQualityChecker()
    
    for check in checks:
        checker.add_check(check)
    
    return checker.run_checks(df) 