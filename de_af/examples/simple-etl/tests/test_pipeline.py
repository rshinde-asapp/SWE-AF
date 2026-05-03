"""Integration tests for simple ETL pipeline."""

import pytest
from pathlib import Path
import csv


class TestSimpleETLPipeline:
    """Test suite for the simple ETL pipeline example."""

    @pytest.fixture
    def csv_data(self):
        """Load CSV data for testing."""
        csv_path = Path(__file__).parent.parent / 'data' / 'users.csv'
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            return list(reader)

    def test_csv_file_exists(self):
        """Test that the source CSV file exists."""
        csv_path = Path(__file__).parent.parent / 'data' / 'users.csv'
        assert csv_path.exists(), "Source CSV file should exist"

    def test_csv_has_correct_columns(self, csv_data):
        """Test that CSV has required columns."""
        required_columns = {'user_id', 'email', 'status', 'created_at'}
        assert set(csv_data[0].keys()) == required_columns, "CSV should have correct columns"

    def test_csv_row_count(self, csv_data):
        """Test that CSV has expected number of rows."""
        assert len(csv_data) == 10, "CSV should have 10 user records"

    def test_no_null_user_ids(self, csv_data):
        """Test that user_id column has no null values."""
        for row in csv_data:
            assert row['user_id'] and row['user_id'].strip(), "All user_ids should be non-null"

    def test_no_null_emails(self, csv_data):
        """Test that email column has no null values."""
        for row in csv_data:
            assert row['email'] and row['email'].strip(), "All emails should be non-null"

    def test_valid_status_values(self, csv_data):
        """Test that status values are within allowed set."""
        valid_statuses = {'active', 'inactive', 'suspended'}
        actual_statuses = {row['status'] for row in csv_data}

        assert actual_statuses.issubset(valid_statuses), \
            f"All status values should be in {valid_statuses}"

    def test_unique_user_ids(self, csv_data):
        """Test that user_id values are unique."""
        user_ids = [row['user_id'] for row in csv_data]
        assert len(user_ids) == len(set(user_ids)), "User IDs should be unique"

    def test_email_format(self, csv_data):
        """Test that email addresses contain @ symbol."""
        for row in csv_data:
            assert '@' in row['email'], f"Email {row['email']} should contain @ symbol"

    def test_dbt_project_yml_exists(self):
        """Test that dbt_project.yml exists."""
        dbt_yml = Path(__file__).parent.parent / 'dbt_project' / 'dbt_project.yml'
        assert dbt_yml.exists(), "dbt_project.yml should exist"

    def test_staging_schema_yml_exists(self):
        """Test that staging schema.yml exists with tests."""
        schema_yml = Path(__file__).parent.parent / 'dbt_project' / 'models' / 'staging' / 'schema.yml'
        assert schema_yml.exists(), "Staging schema.yml should exist"

        content = schema_yml.read_text()
        assert 'unique' in content, "Schema should include unique test"
        assert 'not_null' in content, "Schema should include not_null test"
        assert 'accepted_values' in content, "Schema should include accepted_values test"

    def test_airflow_dag_exists(self):
        """Test that Airflow DAG file exists."""
        dag_path = Path(__file__).parent.parent / 'airflow' / 'dags' / 'simple_etl_dag.py'
        assert dag_path.exists(), "Airflow DAG should exist"

    def test_airflow_dag_has_five_tasks(self):
        """Test that Airflow DAG defines 5 tasks."""
        dag_path = Path(__file__).parent.parent / 'airflow' / 'dags' / 'simple_etl_dag.py'
        content = dag_path.read_text()

        task_count = content.count('task_id=')
        assert task_count == 5, f"DAG should have 5 tasks, found {task_count}"

    def test_terraform_files_exist(self):
        """Test that Terraform configuration files exist."""
        terraform_dir = Path(__file__).parent.parent / 'terraform'

        assert (terraform_dir / 'main.tf').exists(), "main.tf should exist"
        assert (terraform_dir / 'warehouse.tf').exists(), "warehouse.tf should exist"
        assert (terraform_dir / 'variables.tf').exists(), "variables.tf should exist"

    def test_great_expectations_config_exists(self):
        """Test that Great Expectations configuration exists."""
        ge_yml = Path(__file__).parent.parent / 'great_expectations' / 'great_expectations.yml'
        assert ge_yml.exists(), "great_expectations.yml should exist"

    def test_expectations_suite_exists(self):
        """Test that expectations suite exists."""
        suite_path = Path(__file__).parent.parent / 'great_expectations' / 'expectations' / 'users_suite.json'
        assert suite_path.exists(), "users_suite.json should exist"
