"""
Tests for SparkService.
"""

import pytest
import os
from unittest.mock import MagicMock, patch, Mock
from pyspark.sql import SparkSession
from pyspark import SparkConf

from app.services.spark_service import SparkService, get_spark_service


class TestSparkServiceInitialization:
    """Test cases for SparkService initialization and configuration."""

    @patch("app.services.spark_service.SparkSession")
    @patch("app.services.spark_service.SparkConf")
    @patch("multiprocessing.cpu_count")
    def test_initialize_spark_default_config(self, mock_cpu_count, mock_conf_class, mock_session_class):
        """Test Spark initialization with default configuration."""
        mock_cpu_count.return_value = 4
        
        mock_conf = MagicMock()
        mock_conf_class.return_value = mock_conf
        
        mock_session = MagicMock()
        mock_session.version = "3.5.0"
        mock_session.sparkContext.setLogLevel = MagicMock()
        mock_session.builder.config.return_value.getOrCreate.return_value = mock_session
        mock_session_class.builder = MagicMock()
        mock_session_class.builder.config.return_value.getOrCreate.return_value = mock_session
        
        with patch.dict(os.environ, {}, clear=False):
            # Remove any existing Spark env vars
            for key in ["SPARK_DRIVER_MEMORY", "SPARK_EXECUTOR_MEMORY", "SPARK_MAX_RESULT_SIZE", "SPARK_SHUFFLE_PARTITIONS", "DATA_DIR"]:
                os.environ.pop(key, None)
            
            service = SparkService()
            
            # Verify SparkConf was created
            mock_conf_class.assert_called_once()
            
            # Verify configuration settings were set
            assert mock_conf.set.call_count > 0
            
            # Check that default values were used
            set_calls = [call[0] for call in mock_conf.set.call_args_list]
            assert ("spark.driver.memory", "2g") in set_calls
            assert ("spark.executor.memory", "2g") in set_calls
            assert ("spark.driver.maxResultSize", "1g") in set_calls
            assert ("spark.sql.shuffle.partitions", "200") in set_calls
            assert ("spark.default.parallelism", "8") in set_calls  # 4 * 2
            
            # Check AQE settings
            assert ("spark.sql.adaptive.enabled", "true") in set_calls
            assert ("spark.sql.adaptive.coalescePartitions.enabled", "true") in set_calls
            assert ("spark.sql.adaptive.skewJoin.enabled", "true") in set_calls
            
            # Check partition size settings
            assert ("spark.sql.files.maxPartitionBytes", "134217728") in set_calls
            assert ("spark.sql.files.openCostInBytes", "4194304") in set_calls
            
            service.stop()

    @patch("app.services.spark_service.SparkSession")
    @patch("app.services.spark_service.SparkConf")
    @patch("multiprocessing.cpu_count")
    def test_initialize_spark_custom_env_vars(self, mock_cpu_count, mock_conf_class, mock_session_class):
        """Test Spark initialization with custom environment variables."""
        mock_cpu_count.return_value = 8
        
        mock_conf = MagicMock()
        mock_conf_class.return_value = mock_conf
        
        mock_session = MagicMock()
        mock_session.version = "3.5.0"
        mock_session.sparkContext.setLogLevel = MagicMock()
        mock_session.builder.config.return_value.getOrCreate.return_value = mock_session
        mock_session_class.builder = MagicMock()
        mock_session_class.builder.config.return_value.getOrCreate.return_value = mock_session
        
        with patch.dict(os.environ, {
            "SPARK_DRIVER_MEMORY": "4g",
            "SPARK_EXECUTOR_MEMORY": "4g",
            "SPARK_MAX_RESULT_SIZE": "2g",
            "SPARK_SHUFFLE_PARTITIONS": "400",
            "DATA_DIR": "/custom/data"
        }):
            service = SparkService()
            
            # Verify custom values were used
            set_calls = [call[0] for call in mock_conf.set.call_args_list]
            assert ("spark.driver.memory", "4g") in set_calls
            assert ("spark.executor.memory", "4g") in set_calls
            assert ("spark.driver.maxResultSize", "2g") in set_calls
            assert ("spark.sql.shuffle.partitions", "400") in set_calls
            assert ("spark.default.parallelism", "16") in set_calls  # 8 * 2
            assert ("spark.sql.warehouse.dir", "/custom/data/warehouse") in set_calls
            
            service.stop()

    @patch("app.services.spark_service.SparkSession")
    @patch("app.services.spark_service.SparkConf")
    def test_initialize_spark_error_handling(self, mock_conf_class, mock_session_class):
        """Test Spark initialization error handling."""
        mock_conf = MagicMock()
        mock_conf_class.return_value = mock_conf
        
        mock_session_class.builder.config.return_value.getOrCreate.side_effect = Exception("Spark init failed")
        
        with patch.dict(os.environ, {}, clear=False):
            for key in ["SPARK_DRIVER_MEMORY", "SPARK_EXECUTOR_MEMORY", "SPARK_MAX_RESULT_SIZE", "SPARK_SHUFFLE_PARTITIONS", "DATA_DIR"]:
                os.environ.pop(key, None)
            
            with pytest.raises(Exception, match="Spark init failed"):
                SparkService()


class TestSparkServiceProperties:
    """Test cases for SparkService properties and methods."""

    @pytest.fixture
    def mock_spark_session(self):
        """Create a mock SparkSession."""
        mock_session = MagicMock()
        mock_session.version = "3.5.0"
        mock_session.sparkContext.setLogLevel = MagicMock()
        return mock_session

    def test_spark_property_success(self, mock_spark_session):
        """Test accessing spark property when session exists."""
        service = SparkService.__new__(SparkService)
        service._spark_session = mock_spark_session
        
        result = service.spark
        assert result == mock_spark_session

    def test_spark_property_not_initialized(self):
        """Test accessing spark property when session is not initialized."""
        service = SparkService.__new__(SparkService)
        service._spark_session = None
        
        with pytest.raises(RuntimeError, match="SparkSession is not initialized"):
            _ = service.spark

    def test_is_available_true(self, mock_spark_session):
        """Test is_available returns True when Spark is working."""
        service = SparkService.__new__(SparkService)
        service._spark_session = mock_spark_session
        
        mock_df = MagicMock()
        mock_df.count.return_value = 1
        mock_spark_session.createDataFrame.return_value = mock_df
        
        result = service.is_available()
        assert result is True

    def test_is_available_false_no_session(self):
        """Test is_available returns False when session is None."""
        service = SparkService.__new__(SparkService)
        service._spark_session = None
        
        result = service.is_available()
        assert result is False

    def test_is_available_false_on_error(self, mock_spark_session):
        """Test is_available returns False when Spark operation fails."""
        service = SparkService.__new__(SparkService)
        service._spark_session = mock_spark_session
        
        mock_spark_session.createDataFrame.side_effect = Exception("Spark error")
        
        result = service.is_available()
        assert result is False

    def test_stop_success(self, mock_spark_session):
        """Test stopping SparkSession successfully."""
        service = SparkService.__new__(SparkService)
        service._spark_session = mock_spark_session
        
        service.stop()
        
        mock_spark_session.stop.assert_called_once()
        assert service._spark_session is None

    def test_stop_with_error(self, mock_spark_session):
        """Test stopping SparkSession when error occurs."""
        service = SparkService.__new__(SparkService)
        service._spark_session = mock_spark_session
        
        mock_spark_session.stop.side_effect = Exception("Stop error")
        
        service.stop()
        
        # Should still set session to None even on error
        assert service._spark_session is None

    def test_stop_no_session(self):
        """Test stopping when session is None."""
        service = SparkService.__new__(SparkService)
        service._spark_session = None
        
        # Should not raise error
        service.stop()


class TestSparkServiceSingleton:
    """Test cases for SparkService singleton pattern."""

    @patch("app.services.spark_service.SparkService")
    def test_get_spark_service_creates_instance(self, mock_service_class):
        """Test get_spark_service creates new instance when none exists."""
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        
        # Reset singleton
        import app.services.spark_service
        app.services.spark_service._spark_service = None
        
        result = get_spark_service()
        
        assert result == mock_service
        mock_service_class.assert_called_once()

    @patch("app.services.spark_service.SparkService")
    def test_get_spark_service_returns_existing(self, mock_service_class):
        """Test get_spark_service returns existing instance."""
        mock_service = MagicMock()
        
        # Set singleton
        import app.services.spark_service
        app.services.spark_service._spark_service = mock_service
        
        result = get_spark_service()
        
        assert result == mock_service
        mock_service_class.assert_not_called()

