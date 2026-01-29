"""
Spark service for batch processing and analytics.
"""

import os
import logging
from typing import Optional
from pyspark.sql import SparkSession
from pyspark import SparkConf

logger = logging.getLogger(__name__)


class SparkService:
    """Service for managing Spark sessions and operations."""

    def __init__(self):
        """Initialize Spark service with SparkSession."""
        self._spark_session: Optional[SparkSession] = None
        self._initialize_spark()

    def _initialize_spark(self) -> None:
        """
        Initialize SparkSession with appropriate configuration for Docker deployment.

        Configures Spark for local mode with optimized settings for containerized environment.
        Includes performance tuning for adaptive query execution, partition management, and memory optimization.
        """
        try:
            # Get data directory from environment (defaults to /app/data)
            data_dir = os.getenv("DATA_DIR", "/app/data")

            # Get Spark configuration from environment variables with defaults
            driver_memory = os.getenv("SPARK_DRIVER_MEMORY", "2g")
            executor_memory = os.getenv("SPARK_EXECUTOR_MEMORY", "2g")
            max_result_size = os.getenv("SPARK_MAX_RESULT_SIZE", "1g")
            shuffle_partitions = os.getenv("SPARK_SHUFFLE_PARTITIONS", "200")

            # Get CPU count for parallelism
            import multiprocessing

            cpu_count = multiprocessing.cpu_count()

            # Create Spark configuration
            conf = SparkConf()
            conf.set("spark.master", "local[*]")
            conf.set("spark.app.name", "SimpleFREDSite")
            conf.set("spark.sql.warehouse.dir", f"{data_dir}/warehouse")

            # Arrow optimization for pandas interoperability
            conf.set("spark.sql.execution.arrow.pyspark.enabled", "true")
            conf.set("spark.sql.execution.arrow.maxRecordsPerBatch", "10000")

            # Memory settings (configurable via environment variables)
            conf.set("spark.driver.memory", driver_memory)
            conf.set("spark.driver.maxResultSize", max_result_size)
            conf.set("spark.executor.memory", executor_memory)

            # Parallelism and partition settings
            conf.set("spark.default.parallelism", str(cpu_count * 2))
            conf.set("spark.sql.shuffle.partitions", shuffle_partitions)

            # Adaptive query execution (AQE) for better performance
            conf.set("spark.sql.adaptive.enabled", "true")
            conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
            conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
            conf.set("spark.sql.adaptive.coalescePartitions.minPartitionNum", "1")
            conf.set("spark.sql.adaptive.coalescePartitions.initialPartitionNum", "200")

            # Partition size optimization
            conf.set("spark.sql.files.maxPartitionBytes", "134217728")  # 128MB
            conf.set("spark.sql.files.openCostInBytes", "4194304")  # 4MB

            # Serialization
            conf.set("spark.serializer", "org.apache.spark.serializer.KryoSerializer")

            # Logging
            conf.set(
                "spark.eventLog.enabled", "false"
            )  # Disable event log for local mode

            # Create SparkSession
            self._spark_session = SparkSession.builder.config(conf=conf).getOrCreate()

            # Set log level to WARN to reduce verbosity
            self._spark_session.sparkContext.setLogLevel("WARN")

            logger.info("SparkSession initialized successfully")
            logger.info(f"Spark version: {self._spark_session.version}")
            logger.info(f"Data directory: {data_dir}")
            logger.info(
                f"Driver memory: {driver_memory}, Executor memory: {executor_memory}"
            )
            logger.info(
                f"Default parallelism: {cpu_count * 2}, Shuffle partitions: {shuffle_partitions}"
            )
            logger.info("Adaptive query execution (AQE) enabled")

        except Exception as e:
            logger.error(f"Failed to initialize SparkSession: {str(e)}", exc_info=True)
            raise

    @property
    def spark(self) -> SparkSession:
        """
        Get the SparkSession instance.

        Returns:
            SparkSession instance

        Raises:
            RuntimeError: If SparkSession is not initialized
        """
        if self._spark_session is None:
            raise RuntimeError("SparkSession is not initialized")
        return self._spark_session

    def is_available(self) -> bool:
        """
        Check if Spark is available and ready.

        Returns:
            True if Spark is available, False otherwise
        """
        try:
            if self._spark_session is None:
                return False
            # Try a simple operation to verify Spark is working
            test_df = self._spark_session.createDataFrame([(1, "test")], ["id", "name"])
            test_df.count()
            return True
        except Exception as e:
            logger.warning(f"Spark availability check failed: {str(e)}")
            return False

    def stop(self) -> None:
        """Stop the SparkSession and clean up resources."""
        if self._spark_session is not None:
            try:
                self._spark_session.stop()
                logger.info("SparkSession stopped successfully")
            except Exception as e:
                logger.error(f"Error stopping SparkSession: {str(e)}", exc_info=True)
            finally:
                self._spark_session = None

    def __del__(self):
        """Cleanup when service is destroyed."""
        self.stop()


# Singleton instance
_spark_service: Optional[SparkService] = None


def get_spark_service() -> SparkService:
    """
    Get or create Spark service instance (singleton pattern).

    Returns:
        SparkService instance
    """
    global _spark_service
    if _spark_service is None:
        _spark_service = SparkService()
    return _spark_service
