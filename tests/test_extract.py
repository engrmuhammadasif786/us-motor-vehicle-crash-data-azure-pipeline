"""Unit tests for FARS extraction tasks."""

import os
import tempfile

import pandas as pd
import pytest

from pipelines.prefect.tasks.extract import read_accident_csv


class TestReadAccidentCsv:
    """Tests for read_accident_csv task."""

    def test_reads_valid_csv(self):
        """Should read a valid CSV file into a DataFrame."""
        df_input = pd.DataFrame({
            "st_case": [1, 2],
            "year": [2022, 2022],
            "month": [1, 2],
            "day": [10, 20],
            "state_name": ["California", "Texas"],
        })
        
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            df_input.to_csv(f.name, index=False)
            temp_path = f.name
        
        try:
            df_result = read_accident_csv.fn(csv_path=temp_path)
            assert len(df_result) == 2
            assert list(df_result.columns) == list(df_input.columns)
        finally:
            os.remove(temp_path)

    def test_raises_on_missing_file(self):
        """Should raise FileNotFoundError for non-existent file."""
        with pytest.raises(FileNotFoundError):
            read_accident_csv.fn(csv_path="/nonexistent/path/accident.csv")
