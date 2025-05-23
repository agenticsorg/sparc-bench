# Benchmark Orchestrator Workflow Patterns

## Core Delegation Patterns

### 1. SWE-bench Task Classification

```python
def classify_swe_task(problem_statement):
    """Route SWE-bench tasks to appropriate roocode modes"""
    problem = problem_statement.lower()
    
    if any(word in problem for word in ['test', 'testing', 'unittest', 'pytest']):
        return 'tdd'
    elif any(word in problem for word in ['security', 'vulnerability', 'auth', 'permission']):
        return 'security-review'
    elif any(word in problem for word in ['debug', 'error', 'exception', 'traceback', 'bug']):
        return 'debug'
    elif any(word in problem for word in ['integrate', 'merge', 'combine', 'connect']):
        return 'integration'
    else:
        return 'code'  # Default to auto-coder for general implementation
```

### 2. Task Delegation Template

```
new_task('{mode}', '''
# SWE-bench Task: {instance_id}

## Repository: {repo}

## Problem Statement
{problem_statement}

## Implementation Hints
{hints_text}

## Your Task
You are the {mode} mode in the roocode SPARC system. Please solve this software engineering issue by:

1. **Analysis**: Understand the problem and identify the root cause
2. **Investigation**: Locate the relevant files and problematic code
3. **Solution**: Implement a proper fix for the issue
4. **Verification**: Ensure your solution works and doesn't break existing functionality

## Requirements
- Provide working code that fixes the described issue
- Follow the repository's coding standards and patterns
- Include appropriate error handling
- Ensure backward compatibility
- Write clear, maintainable code

Begin your implementation now.
''')
```

## Result Collection Patterns

### 1. Task Result Processing

```python
def process_task_result(task_id, mode_result):
    """Process completed task result from roocode mode"""
    return {
        'instance_id': task_id,
        'mode_used': mode_result.get('mode', 'unknown'),
        'status': mode_result.get('status', 'unknown'),
        'solution_provided': mode_result.get('solution_provided', False),
        'files_modified': mode_result.get('files_modified', []),
        'verification_passed': mode_result.get('verification_passed', False),
        'execution_time': mode_result.get('execution_time', 0),
        'quality_score': calculate_quality_score(mode_result),
        'completion_details': mode_result
    }
```

### 2. Aggregate Metrics Calculation

```python
def calculate_benchmark_metrics(results):
    """Calculate comprehensive benchmark metrics"""
    total_tasks = len(results)
    completed_tasks = len([r for r in results if r['solution_provided']])
    
    return {
        'total_tasks': total_tasks,
        'completed_successfully': completed_tasks,
        'completion_rate': f"{(completed_tasks/total_tasks)*100:.1f}%",
        'mode_distribution': calculate_mode_usage(results),
        'average_quality': calculate_average_quality(results),
        'performance_trends': analyze_performance_trends(results)
    }
```

## Orchestration State Management

### 1. Workflow State Tracking

```python
class BenchmarkOrchestrator:
    def __init__(self):
        self.state = {
            'current_phase': 'initialization',
            'total_tasks': 0,
            'completed_tasks': 0,
            'active_delegations': {},
            'results': [],
            'start_time': None,
            'phase_history': []
        }
    
    def update_phase(self, new_phase):
        """Update orchestration phase with history tracking"""
        self.state['phase_history'].append({
            'phase': self.state['current_phase'],
            'completed_at': datetime.now(),
            'tasks_completed': self.state['completed_tasks']
        })
        self.state['current_phase'] = new_phase
```

### 2. Progress Monitoring

```python
def monitor_progress(orchestrator):
    """Generate real-time progress report"""
    return {
        'current_phase': orchestrator.state['current_phase'],
        'progress_percentage': (orchestrator.state['completed_tasks'] / 
                              orchestrator.state['total_tasks']) * 100,
        'active_delegations': len(orchestrator.state['active_delegations']),
        'estimated_completion': calculate_eta(orchestrator.state),
        'performance_summary': generate_performance_summary(orchestrator.state)
    }
```

## Error Handling Patterns

### 1. Graceful Failure Management

```python
def handle_task_failure(task_id, error_details):
    """Handle individual task failures gracefully"""
    return {
        'instance_id': task_id,
        'status': 'failed',
        'error_type': classify_error(error_details),
        'error_message': str(error_details),
        'retry_recommended': should_retry(error_details),
        'fallback_mode': suggest_fallback_mode(error_details)
    }
```

### 2. Recovery Procedures

```python
def implement_recovery(failed_tasks):
    """Implement recovery procedures for failed tasks"""
    for task in failed_tasks:
        if task['retry_recommended']:
            # Retry with same mode
            retry_task(task['instance_id'], task['original_mode'])
        elif task['fallback_mode']:
            # Try different mode
            delegate_task(task['instance_id'], task['fallback_mode'])
        else:
            # Mark as permanently failed
            mark_task_failed(task['instance_id'])
```

## Quality Assurance Patterns

### 1. Solution Validation

```python
def validate_solution(task_result):
    """Validate the quality of a completed solution"""
    quality_metrics = {
        'code_quality': assess_code_quality(task_result),
        'test_coverage': check_test_coverage(task_result),
        'documentation': validate_documentation(task_result),
        'security': check_security_practices(task_result),
        'performance': assess_performance_impact(task_result)
    }
    
    return calculate_overall_quality(quality_metrics)
```

### 2. Continuous Improvement

```python
def analyze_patterns(completed_tasks):
    """Analyze patterns in completed tasks for improvement"""
    return {
        'successful_patterns': identify_success_patterns(completed_tasks),
        'failure_patterns': identify_failure_patterns(completed_tasks),
        'mode_effectiveness': analyze_mode_effectiveness(completed_tasks),
        'improvement_recommendations': generate_recommendations(completed_tasks)
    }
```

## Reporting Patterns

### 1. Comprehensive Report Generation

```python
def generate_benchmark_report(orchestrator_state):
    """Generate comprehensive benchmark report"""
    return {
        'executive_summary': create_executive_summary(orchestrator_state),
        'detailed_metrics': calculate_detailed_metrics(orchestrator_state),
        'task_analysis': analyze_individual_tasks(orchestrator_state),
        'mode_performance': analyze_mode_performance(orchestrator_state),
        'recommendations': generate_improvement_recommendations(orchestrator_state),
        'methodology': document_methodology(orchestrator_state)
    }
```

### 2. Real-time Dashboard

```python
def create_dashboard_data(orchestrator_state):
    """Create real-time dashboard data"""
    return {
        'current_status': get_current_status(orchestrator_state),
        'progress_charts': generate_progress_charts(orchestrator_state),
        'performance_metrics': get_live_metrics(orchestrator_state),
        'recent_completions': get_recent_completions(orchestrator_state),
        'system_health': check_system_health(orchestrator_state)
    }