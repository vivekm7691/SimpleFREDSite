# Performance Optimization Recommendations for Analytics Endpoint

**Date:** 2026-01-23  
**Context:** High response times observed in `/api/spark/analytics` endpoint  
**Status:** Recommendations for future implementation

---

## Possible Reasons for High Response Time

### 1. **FRED API Latency**
**Issue:** External HTTP calls to FRED API introduce network latency and potential rate limiting.

**Improvements:**
- ✅ Use caching (`use_cache=true`) to avoid repeated API calls
- ✅ Increase cache hit rate by standardizing limit/sort_order parameters
- ✅ Implement request batching if FRED API supports it
- ✅ Add connection pooling and keep-alive for HTTP connections

---

### 2. **Multiple `df.count()` Calls**
**Issue:** `count()` triggers a full DataFrame scan each time it's called. Currently called in:
- `_prepare_dataframe_for_analytics()`
- `calculate_statistics()`
- `calculate_growth_rates()`
- `calculate_correlations()`
- `calculate_moving_averages()`
- `calculate_time_aggregations()`

**Improvements:**
- Cache the count result once and reuse it
- Use lazy evaluation - avoid calling `count()` unless absolutely necessary
- Cache the DataFrame after preparation to avoid re-counting

---

### 3. **Multiple `collect()` Operations**
**Issue:** `collect()` brings all data to the driver, which is expensive. Currently called:
- `df.select("series_id").distinct().collect()` - to get unique series IDs
- `stats_df.collect()` - to get statistics results
- `series_df.collect()` - in growth rates calculation
- `pivoted_df.select(...).collect()` - in correlations
- `df_agg.select(...).collect()` - in time aggregations

**Improvements:**
- Minimize `collect()` calls - use Spark operations instead
- For small results, cache the DataFrame and reuse
- Use `take()` or `head()` instead of `collect()` when only a few rows needed
- Cache unique series IDs after first collection

---

### 4. **Sequential Processing of Analytics**
**Issue:** Analytics are processed sequentially even when they could be parallelized. Each analytics type processes the DataFrame separately.

**Improvements:**
- Run independent analytics in parallel (e.g., statistics and correlations can run simultaneously)
- Use Spark's parallel execution within a single DataFrame operation
- Consider async/await for independent operations

---

### 5. **Inefficient DataFrame Operations**
**Issue:** 
- `_prepare_dataframe_for_analytics()` is called multiple times (checked in each method)
- Multiple filters and window operations
- Pivot operations for correlations can be expensive

**Improvements:**
- Prepare DataFrame once at endpoint level and pass to all methods
- Cache the prepared DataFrame
- Optimize window functions - use partitioning and ordering efficiently
- For correlations, consider pre-computing or caching pivot results

---

### 6. **Cache I/O Operations**
**Issue:** Reading/writing Parquet files synchronously can be slow, especially on network storage.

**Improvements:**
- Use async I/O for cache operations
- Implement cache warming for frequently accessed series
- Use faster storage (SSD) for cache directory
- Consider in-memory caching for hot data

---

### 7. **Spark JVM Overhead**
**Issue:** JVM startup, warmup, memory allocation, and garbage collection can add latency.

**Improvements:**
- Keep SparkSession alive (already done via singleton)
- Tune Spark memory settings (driver/executor memory)
- Optimize GC settings
- Use Spark's columnar processing when possible

---

### 8. **Data Conversion Overhead**
**Issue:** Converting between Python objects and Spark DataFrames, and converting results back to Python dictionaries adds overhead.

**Improvements:**
- Minimize conversions - work with DataFrames as long as possible
- Use Spark SQL for aggregations instead of Python loops
- Batch convert results instead of row-by-row
- Consider using Arrow for faster data transfer

---

### 9. **Growth Rates: Per-Series Processing**
**Issue:** Loops over series IDs and processes each separately, with multiple DataFrame operations per series.

**Improvements:**
- Process all series in a single DataFrame operation using window functions
- Use Spark's `groupBy` and window functions instead of Python loops
- Vectorize operations where possible

---

### 10. **Correlations: Nested Loops**
**Issue:** Nested loops over series pairs with multiple correlation calculations.

**Improvements:**
- Use Spark's built-in correlation matrix functions
- Compute all correlations in a single operation
- Cache pivot results if computing multiple analytics

---

### 11. **Large Data Volumes**
**Issue:** Processing large datasets (high `limit` values) with multiple analytics operations.

**Improvements:**
- Limit data size early (filter before analytics)
- Use sampling for exploratory analytics
- Implement pagination for results
- Add data partitioning by series_id

---

### 12. **No Result Caching**
**Issue:** Same analytics are recalculated on every request with no caching of computed analytics results.

**Improvements:**
- Cache computed analytics results (Redis or in-memory)
- Cache key: series_ids + analytics_types + parameters
- Set appropriate TTL based on data freshness needs
- Invalidate cache when new data arrives

---

## Priority Recommendations

### High Impact, Low Effort
1. ✅ Cache `df.count()` result
2. ✅ Prepare DataFrame once at endpoint level
3. ✅ Cache unique series IDs
4. ✅ Use `use_cache=true` consistently

### High Impact, Medium Effort
1. ✅ Minimize `collect()` calls
2. ✅ Process all series together in growth rates
3. ✅ Cache prepared DataFrame
4. ✅ Run independent analytics in parallel

### Medium Impact, High Effort
1. ✅ Implement analytics result caching
2. ✅ Optimize correlation calculations
3. ✅ Async cache I/O operations
4. ✅ Spark memory/GC tuning

---

## Implementation Notes

### Quick Wins (Can be implemented immediately)
- **Cache count result:** Store `row_count = df.count()` once and reuse
- **Prepare DataFrame once:** Move `_prepare_dataframe_for_analytics()` call to endpoint level
- **Cache series IDs:** Store unique series IDs after first collection
- **Remove redundant checks:** Remove `df.count() == 0` checks if DataFrame is already validated

### Medium-term Improvements
- **Refactor growth rates:** Process all series in single DataFrame operation
- **Optimize correlations:** Use Spark's correlation matrix instead of nested loops
- **Parallel analytics:** Use asyncio or threading for independent analytics
- **Result caching:** Add Redis or in-memory cache for analytics results

### Long-term Optimizations
- **Spark tuning:** Optimize memory, partitions, and GC settings
- **Async I/O:** Make cache operations asynchronous
- **Data partitioning:** Partition data by series_id for better performance
- **Monitoring:** Add performance metrics and profiling

---

## Files to Modify

### Primary Files
- `backend/app/api/routes.py` - Analytics endpoint
- `backend/app/services/spark_data_service.py` - Analytics methods

### Potential New Files
- `backend/app/services/analytics_cache_service.py` - Analytics result caching
- `backend/app/config/spark_config.py` - Spark optimization settings

---

## Testing Recommendations

After implementing optimizations:
1. Benchmark response times before and after
2. Test with various data sizes (limit: 10, 50, 100, 500, 1000)
3. Test with multiple series (1, 2, 5, 10, 20)
4. Test with different analytics combinations
5. Monitor memory usage and GC activity
6. Test cache hit/miss scenarios

---

## Metrics to Track

- Response time (p50, p95, p99)
- Cache hit rate
- DataFrame operation counts
- Memory usage
- GC pause times
- API call counts to FRED

---

## References

- Spark Performance Tuning: https://spark.apache.org/docs/latest/tuning.html
- PySpark Best Practices: https://spark.apache.org/docs/latest/api/python/development/index.html
- FastAPI Performance: https://fastapi.tiangolo.com/advanced/performance/

