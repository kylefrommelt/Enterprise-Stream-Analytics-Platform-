"""
Unit tests for the data quality utilities.
"""

import os
import json
import pandas as pd
import pytest
import datetime
from unittest import mock

# Import the data quality module
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.data_quality import (
    DataQualityCheck, NullCheck, ValueRangeCheck, UniquenessCheck,
    SchemaCheck, AnomalyCheck, DataQualityChecker, load_checks_from_config
)


# Sample test data
@pytest.fixture
def sample_data():
    """Create a sample DataFrame for testing."""
    return pd.DataFrame({
        'id': [1, 2, 3, 4, 5],
        'name': ['Alice', 'Bob', 'Charlie', 'David', None],
        'age': [25, 30, None, 40, 45],
        'score': [95.5, 87.3, 76.8, 92.1, 65.2],
        'active': [True, False, True, True, False]
    })


@pytest.fixture
def sample_with_anomalies():
    """Create a sample DataFrame with anomalies for testing."""
    return pd.DataFrame({
        'id': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'value': [10, 12, 11, 13, 9, 14, 100, 11, 12, 13]  # 100 is an anomaly
    })


class TestDataQualityChecks:
    """Test the data quality check classes."""

    def test_null_check_pass(self, sample_data):
        """Test that the null check passes when nulls are within the threshold."""
        # Setup: Create a null check for the 'id' column with no nulls allowed
        check = NullCheck("id_null_check", ["id"], threshold=0.0)
        
        # Execute: Run the check
        result = check.run(sample_data)
        
        # Verify: Check should pass
        assert result is True
        assert check.passed is True

    def test_null_check_fail(self, sample_data):
        """Test that the null check fails when nulls exceed the threshold."""
        # Setup: Create a null check for the 'name' column with no nulls allowed
        check = NullCheck("name_null_check", ["name"], threshold=0.0)
        
        # Execute: Run the check
        result = check.run(sample_data)
        
        # Verify: Check should fail
        assert result is False
        assert check.passed is False
        assert "too many null values" in check.message.lower()

    def test_null_check_missing_column(self, sample_data):
        """Test that the null check fails when a column is missing."""
        # Setup: Create a null check for a non-existent column
        check = NullCheck("missing_column_check", ["non_existent"], threshold=0.0)
        
        # Execute: Run the check
        result = check.run(sample_data)
        
        # Verify: Check should fail
        assert result is False
        assert check.passed is False
        assert "not found" in check.message.lower()

    def test_value_range_check_pass(self, sample_data):
        """Test that the value range check passes when values are within range."""
        # Setup: Create a value range check for the 'age' column
        check = ValueRangeCheck("age_range_check", {"age": (20, 50)})
        
        # Execute: Run the check
        result = check.run(sample_data)
        
        # Verify: Check should pass
        assert result is True
        assert check.passed is True

    def test_value_range_check_fail(self, sample_data):
        """Test that the value range check fails when values are outside range."""
        # Setup: Create a value range check for the 'score' column with a tight range
        check = ValueRangeCheck("score_range_check", {"score": (80, 90)})
        
        # Execute: Run the check
        result = check.run(sample_data)
        
        # Verify: Check should fail
        assert result is False
        assert check.passed is False
        assert "outside expected ranges" in check.message.lower()

    def test_uniqueness_check_pass(self, sample_data):
        """Test that the uniqueness check passes when values are unique."""
        # Setup: Create a uniqueness check for the 'id' column
        check = UniquenessCheck("id_uniqueness_check", ["id"], should_be_unique=True)
        
        # Execute: Run the check
        result = check.run(sample_data)
        
        # Verify: Check should pass
        assert result is True
        assert check.passed is True

    def test_uniqueness_check_fail(self, sample_data):
        """Test that the uniqueness check fails when duplicates are found."""
        # Modify the sample data to add a duplicate id
        data_with_duplicate = sample_data.copy()
        data_with_duplicate.loc[5] = [1, "Duplicate", 50, 99.9, True]  # Duplicate ID
        
        # Setup: Create a uniqueness check for the 'id' column
        check = UniquenessCheck("id_uniqueness_check", ["id"], should_be_unique=True)
        
        # Execute: Run the check
        result = check.run(data_with_duplicate)
        
        # Verify: Check should fail
        assert result is False
        assert check.passed is False
        assert "duplicate values" in check.message.lower()

    def test_schema_check_pass(self, sample_data):
        """Test that the schema check passes when the schema matches."""
        # Setup: Create a schema check with the expected schema
        expected_schema = {
            'id': 'int',
            'name': 'object',
            'age': 'float',
            'score': 'float',
            'active': 'bool'
        }
        check = SchemaCheck("schema_check", expected_schema)
        
        # Execute: Run the check
        result = check.run(sample_data)
        
        # Verify: Check should pass
        assert result is True
        assert check.passed is True

    def test_schema_check_fail_missing_column(self, sample_data):
        """Test that the schema check fails when a column is missing."""
        # Setup: Create a schema check with an extra column
        expected_schema = {
            'id': 'int',
            'name': 'object',
            'age': 'float',
            'score': 'float',
            'active': 'bool',
            'extra': 'int'  # This column doesn't exist
        }
        check = SchemaCheck("schema_check", expected_schema)
        
        # Execute: Run the check
        result = check.run(sample_data)
        
        # Verify: Check should fail
        assert result is False
        assert check.passed is False
        assert isinstance(check.message, dict)
        assert "extra" in check.message["missing_columns"]

    def test_anomaly_check_pass(self, sample_data):
        """Test that the anomaly check passes when no anomalies are found."""
        # Setup: Create an anomaly check for the 'age' column
        check = AnomalyCheck("age_anomaly_check", "age", method="zscore", threshold=3.0)
        
        # Execute: Run the check
        result = check.run(sample_data)
        
        # Verify: Check should pass
        assert result is True
        assert check.passed is True

    def test_anomaly_check_fail(self, sample_with_anomalies):
        """Test that the anomaly check fails when anomalies are found."""
        # Setup: Create an anomaly check for the 'value' column
        check = AnomalyCheck("value_anomaly_check", "value", method="zscore", threshold=2.0)
        
        # Execute: Run the check
        result = check.run(sample_with_anomalies)
        
        # Verify: Check should fail
        assert result is False
        assert check.passed is False
        assert "anomalies" in check.message.lower()


class TestDataQualityChecker:
    """Test the data quality checker class."""

    def test_checker_runs_all_checks(self, sample_data):
        """Test that the checker runs all checks and returns a summary."""
        # Setup: Create a checker with multiple checks
        checker = DataQualityChecker()
        checker.add_check(NullCheck("id_null_check", ["id"], threshold=0.0))
        checker.add_check(NullCheck("name_null_check", ["name"], threshold=0.0))
        checker.add_check(ValueRangeCheck("age_range_check", {"age": (20, 50)}))
        
        # Execute: Run the checks
        results = checker.run_checks(sample_data)
        
        # Verify: Summary should include all check results
        assert "summary" in results
        assert "results" in results
        assert results["summary"]["total_checks"] == 3
        assert results["summary"]["passed_checks"] == 2
        assert results["summary"]["failed_checks"] == 1
        assert len(results["results"]) == 3

    def test_checker_handles_errors_gracefully(self, sample_data):
        """Test that the checker handles errors in checks gracefully."""
        # Setup: Create a mock check that raises an exception
        mock_check = mock.MagicMock(spec=DataQualityCheck)
        mock_check.name = "error_check"
        mock_check.description = "This check raises an error"
        mock_check.run.side_effect = Exception("Test exception")
        
        # Create a checker with the mock check
        checker = DataQualityChecker()
        checker.add_check(mock_check)
        
        # Execute: Run the checks
        results = checker.run_checks(sample_data)
        
        # Verify: Results should include the error
        assert "summary" in results
        assert "results" in results
        assert results["summary"]["total_checks"] == 1
        assert results["summary"]["passed_checks"] == 0
        assert results["summary"]["failed_checks"] == 1
        assert "Error" in results["results"][0]["message"]


class TestConfigLoading:
    """Test the configuration loading functions."""

    def test_load_checks_from_config(self, tmp_path):
        """Test loading checks from a configuration file."""
        # Setup: Create a temporary config file
        config = {
            "checks": [
                {
                    "name": "id_null_check",
                    "type": "null_check",
                    "columns": ["id"],
                    "threshold": 0.0
                },
                {
                    "name": "age_range_check",
                    "type": "value_range_check",
                    "column_ranges": [
                        {"column": "age", "min": 20, "max": 50}
                    ]
                },
                {
                    "name": "id_uniqueness_check",
                    "type": "uniqueness_check",
                    "columns": ["id"],
                    "should_be_unique": True
                },
                {
                    "name": "schema_check",
                    "type": "schema_check",
                    "expected_schema": {
                        "id": "int",
                        "name": "object"
                    }
                },
                {
                    "name": "age_anomaly_check",
                    "type": "anomaly_check",
                    "column": "age",
                    "method": "zscore",
                    "threshold": 3.0
                }
            ]
        }
        
        config_path = tmp_path / "test_config.yaml"
        with open(config_path, "w") as f:
            import yaml
            yaml.dump(config, f)
        
        # Execute: Load checks from the config
        checks = load_checks_from_config(config_path)
        
        # Verify: Checks should be loaded correctly
        assert len(checks) == 5
        assert isinstance(checks[0], NullCheck)
        assert isinstance(checks[1], ValueRangeCheck)
        assert isinstance(checks[2], UniquenessCheck)
        assert isinstance(checks[3], SchemaCheck)
        assert isinstance(checks[4], AnomalyCheck)


if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 