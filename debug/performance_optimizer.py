#!/usr/bin/env python3
"""Performance optimization and profiling utility."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import time
import cProfile
import pstats
import io
import json
from typing import Dict, List, Any, Callable
from functools import wraps
import psutil
import os


def profile_function(func: Callable) -> Callable:
    """Decorator to profile a function's performance."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()
        
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        try:
            result = func(*args, **kwargs)
        finally:
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            profiler.disable()
        
        # Get profiling stats
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
        ps.print_stats(20)  # Top 20 functions
        
        # Calculate metrics
        duration = end_time - start_time
        memory_used = end_memory - start_memory
        
        print(f"📊 Performance Profile: {func.__name__}")
        print(f"  Duration: {duration:.3f}s")
        print(f"  Memory: {memory_used:.2f}MB")
        print(f"  Profile:\n{s.getvalue()}")
        
        return result
    
    return wrapper


class PerformanceMonitor:
    """Monitor and optimize performance of key operations."""
    
    def __init__(self):
        self.metrics = {}
        self.start_time = None
        self.start_memory = None
    
    def start_monitoring(self, operation_name: str):
        """Start monitoring an operation."""
        self.start_time = time.time()
        self.start_memory = psutil.Process().memory_info().rss / 1024 / 1024
        print(f"🔍 Starting performance monitoring: {operation_name}")
    
    def end_monitoring(self, operation_name: str) -> Dict[str, Any]:
        """End monitoring and return metrics."""
        if self.start_time is None:
            return {}
        
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        duration = end_time - self.start_time
        memory_used = end_memory - self.start_memory
        
        metrics = {
            'operation': operation_name,
            'duration': duration,
            'memory_used_mb': memory_used,
            'memory_peak_mb': end_memory,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        self.metrics[operation_name] = metrics
        
        print(f"📊 {operation_name}: {duration:.3f}s, {memory_used:.2f}MB")
        
        return metrics
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        if not self.metrics:
            return {}
        
        total_duration = sum(m['duration'] for m in self.metrics.values())
        total_memory = sum(m['memory_used_mb'] for m in self.metrics.values())
        
        return {
            'total_operations': len(self.metrics),
            'total_duration': total_duration,
            'total_memory_mb': total_memory,
            'average_duration': total_duration / len(self.metrics),
            'average_memory_mb': total_memory / len(self.metrics),
            'operations': self.metrics
        }


def optimize_text_processing(text: str) -> str:
    """Optimize text processing for better performance."""
    # Remove excessive whitespace
    text = ' '.join(text.split())
    
    # Normalize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Remove duplicate lines
    lines = text.split('\n')
    seen_lines = set()
    unique_lines = []
    
    for line in lines:
        line_stripped = line.strip()
        if line_stripped and line_stripped not in seen_lines:
            seen_lines.add(line_stripped)
            unique_lines.append(line)
    
    return '\n'.join(unique_lines)


def optimize_regex_patterns() -> Dict[str, str]:
    """Optimize regex patterns for better performance."""
    return {
        'creditor_pattern': r'\b[A-Z][A-Z\s&.,\'-]+\b',
        'date_pattern': r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b',
        'account_pattern': r'\b\d{4}[-*\s]?\d{4}[-*\s]?\d{4}[-*\s]?\d{4}\b',
        'balance_pattern': r'\$[\d,]+(?:\.\d{2})?',
        'status_pattern': r'\b(?:Open|Closed|Paid|Collection|Charge-off|Late|Past Due)\b'
    }


def benchmark_operations():
    """Benchmark key operations for performance optimization."""
    print("⚡ Performance Benchmarking...")
    print("=" * 50)
    
    monitor = PerformanceMonitor()
    
    # Test text processing optimization
    test_text = "This is a test text with duplicate lines.\n" * 1000
    test_text += "This is a test text with duplicate lines.\n" * 1000
    
    monitor.start_monitoring("Text Processing - Original")
    original_result = test_text
    monitor.end_monitoring("Text Processing - Original")
    
    monitor.start_monitoring("Text Processing - Optimized")
    optimized_result = optimize_text_processing(test_text)
    monitor.end_monitoring("Text Processing - Optimized")
    
    # Test regex compilation
    import re
    patterns = optimize_regex_patterns()
    
    monitor.start_monitoring("Regex Compilation")
    compiled_patterns = {name: re.compile(pattern, re.IGNORECASE) for name, pattern in patterns.items()}
    monitor.end_monitoring("Regex Compilation")
    
    # Test pattern matching
    sample_text = "BANK OF AMERICA account ending in 1234-5678-9012-3456 with balance $1,234.56"
    
    monitor.start_monitoring("Pattern Matching")
    for name, pattern in compiled_patterns.items():
        matches = pattern.findall(sample_text)
    monitor.end_monitoring("Pattern Matching")
    
    # Get summary
    summary = monitor.get_summary()
    
    print(f"\n📊 Performance Summary:")
    print(f"  Total Operations: {summary['total_operations']}")
    print(f"  Total Duration: {summary['total_duration']:.3f}s")
    print(f"  Total Memory: {summary['total_memory_mb']:.2f}MB")
    print(f"  Average Duration: {summary['average_duration']:.3f}s")
    print(f"  Average Memory: {summary['average_memory_mb']:.2f}MB")
    
    return summary


def optimize_memory_usage():
    """Analyze and optimize memory usage."""
    print("🧠 Memory Usage Optimization...")
    print("=" * 50)
    
    process = psutil.Process()
    initial_memory = process.memory_info().rss / 1024 / 1024
    
    print(f"Initial memory usage: {initial_memory:.2f}MB")
    
    # Monitor memory during operations
    monitor = PerformanceMonitor()
    
    # Test large data structure creation
    monitor.start_monitoring("Large Data Structure")
    large_data = []
    for i in range(10000):
        large_data.append({
            'id': i,
            'name': f'Account {i}',
            'balance': f'${i * 100}',
            'status': 'Open' if i % 2 == 0 else 'Closed'
        })
    monitor.end_monitoring("Large Data Structure")
    
    # Test data filtering
    monitor.start_monitoring("Data Filtering")
    filtered_data = [item for item in large_data if item['status'] == 'Open']
    monitor.end_monitoring("Data Filtering")
    
    # Test data serialization
    monitor.start_monitoring("Data Serialization")
    json_data = json.dumps(large_data)
    monitor.end_monitoring("Data Serialization")
    
    # Clean up
    del large_data
    del filtered_data
    del json_data
    
    final_memory = process.memory_info().rss / 1024 / 1024
    memory_reduction = initial_memory - final_memory
    
    print(f"Final memory usage: {final_memory:.2f}MB")
    print(f"Memory reduction: {memory_reduction:.2f}MB")
    
    return monitor.get_summary()


def generate_optimization_report():
    """Generate comprehensive optimization report."""
    print("📋 Generating Performance Optimization Report...")
    print("=" * 60)
    
    report = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'system_info': {
            'cpu_count': psutil.cpu_count(),
            'memory_total_gb': psutil.virtual_memory().total / 1024 / 1024 / 1024,
            'python_version': sys.version,
            'platform': sys.platform
        },
        'benchmarks': benchmark_operations(),
        'memory_optimization': optimize_memory_usage(),
        'recommendations': []
    }
    
    # Generate recommendations
    if report['benchmarks']['average_duration'] > 1.0:
        report['recommendations'].append("Consider caching frequently accessed data")
    
    if report['benchmarks']['average_memory_mb'] > 100:
        report['recommendations'].append("Implement memory-efficient data structures")
    
    if report['memory_optimization']['total_memory_mb'] > 500:
        report['recommendations'].append("Use generators for large data processing")
    
    # Save report
    report_file = Path("performance_optimization_report.json")
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Performance report saved to: {report_file}")
    
    # Print recommendations
    if report['recommendations']:
        print(f"\n💡 Optimization Recommendations:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"  {i}. {rec}")
    
    return report


def main():
    """Main function for performance optimization."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Performance optimization utility')
    parser.add_argument('--benchmark', action='store_true', help='Run performance benchmarks')
    parser.add_argument('--memory', action='store_true', help='Analyze memory usage')
    parser.add_argument('--report', action='store_true', help='Generate comprehensive report')
    parser.add_argument('--all', action='store_true', help='Run all optimizations')
    
    args = parser.parse_args()
    
    if args.all or not any([args.benchmark, args.memory, args.report]):
        generate_optimization_report()
    else:
        if args.benchmark:
            benchmark_operations()
        if args.memory:
            optimize_memory_usage()
        if args.report:
            generate_optimization_report()


if __name__ == "__main__":
    main()
