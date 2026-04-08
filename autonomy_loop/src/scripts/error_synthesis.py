import json
from datetime import datetime

def synthesize_errors(log_file_path):
    with open(log_file_path, 'r') as f:
        logs = [json.loads(line) for line in f]
    
    report = {
        "generated_at": datetime.now().isoformat(),
        "summary": {},
        "recommendations": []
    }
    
    for log in logs:
        category = log.get('category', 'unknown')
        report['summary'][category] = report['summary'].get(category, 0) + 1
    
    return json.dumps(report, indent=2)

if __name__ == '__main__':
    print(synthesize_errors('logs/system.log'))