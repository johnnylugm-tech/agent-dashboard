"""
Monitor Skill 使用範例

演示如何整合錯誤分類、日誌、健康檢查
"""

import sys
import os

# Add the skills/monitor directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

# Direct imports from the local modules
from __init__ import AgentMonitor
from errors import ErrorClassifier


def example_basic():
    """基本使用"""
    print("=" * 50)
    print("Example 1: Basic Usage")
    print("=" * 50)
    
    # 初始化監控器
    monitor = AgentMonitor(
        agent_id="demo-agent",
        log_path="./logs"
    )
    
    # 開始任務
    task_id = monitor.task_start(
        task_name="分析數據",
        context={"user_id": "user-123"}
    )
    print(f"Task started: {task_id}")
    
    # 模擬任務執行
    import time
    time.sleep(0.1)
    
    # 任務完成
    monitor.task_complete(
        task_id=task_id,
        result={"status": "success", "rows": 100}
    )
    print("Task completed!")
    
    # 健康檢查
    health = monitor.health_check()
    print(f"Health: {health['status']}")
    print()


def example_error_classification():
    """錯誤分類範例"""
    print("=" * 50)
    print("Example 2: Error Classification")
    print("=" * 50)
    
    classifier = ErrorClassifier()
    
    # 測試不同錯誤
    test_errors = [
        {"code": "E1001", "message": "Invalid input"},
        {"code": "E2003", "message": "Tool timeout"},
        {"code": "E3001", "message": "Execution failed"},
        {"code": "E4001", "message": "System overload"},
    ]
    
    for error in test_errors:
        result = classifier.classify(error)
        print(f"Error: {error['code']}")
        print(f"  Level: {result['level']}")
        print(f"  Action: {result['action']}")
        print(f"  Description: {result['description']}")
        print()


def example_with_error_handling():
    """錯誤處理範例"""
    print("=" * 50)
    print("Example 3: Error Handling")
    print("=" * 50)
    
    monitor = AgentMonitor(
        agent_id="error-demo",
        log_path="./logs"
    )
    
    task_id = monitor.task_start(task_name="Risky Operation")
    
    # 模擬錯誤
    error = {"code": "E2002", "message": "Tool execution failed"}
    monitor.task_error(task_id, error)
    
    # 健康檢查
    health = monitor.health_check()
    print(f"Health after error: {health['status']}")
    print(f"Error rate: {health['checks']['error_rate']['value']}")
    print()


def example_reflection_pattern():
    """Reflection Pattern 範例"""
    print("=" * 50)
    print("Example 4: Reflection Pattern")
    print("=" * 50)
    
    monitor = AgentMonitor(
        agent_id="reflection-demo",
        log_path="./logs"
    )
    
    def execute_with_reflection(task_fn, *args, **kwargs):
        """Reflection Pattern 實現"""
        task_id = monitor.task_start(
            task_name=task_fn.__name__,
            context={"args": str(args), "kwargs": str(kwargs)}
        )
        
        try:
            # 執行
            result = task_fn(*args, **kwargs)
            
            # 自我審查（Reflection）
            health = monitor.health_check()
            if health["status"] == "unhealthy":
                raise Exception(f"Health check failed: {health['status']}")
            
            # 完成
            monitor.task_complete(task_id, result={"data": result})
            return result
            
        except Exception as e:
            # 錯誤處理
            monitor.task_error(task_id, error={"message": str(e)})
            raise
    
    # 模擬任務
    def sample_task():
        return {"result": "success"}
    
    result = execute_with_reflection(sample_task)
    print(f"Result: {result}")
    print()


def example_reporting():
    """報告範例"""
    print("=" * 50)
    print("Example 5: Reporting")
    print("=" * 50)
    
    monitor = AgentMonitor(
        agent_id="report-demo",
        log_path="./logs"
    )
    
    # 執行多個任務
    for i in range(5):
        task_id = monitor.task_start(task_name=f"Task {i}")
        monitor.task_complete(task_id, result={"index": i})
    
    # 生成報告
    report = monitor.generate_report("hourly")
    print(f"Report type: {report['report_type']}")
    print(f"Total tasks: {report['summary']['total_tasks']}")
    print(f"Success rate: {report['summary']['success_rate']}")
    print()


if __name__ == "__main__":
    example_basic()
    example_error_classification()
    example_with_error_handling()
    example_reflection_pattern()
    example_reporting()
    
    print("=" * 50)
    print("All examples completed!")
    print("=" * 50)
