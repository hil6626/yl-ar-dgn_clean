#!/usr/bin/env python3
"""
Deployment Notification Script
Sends deployment notifications to Slack and other channels
"""

import sys
import json
import requests
from datetime import datetime
from typing import Dict, Any


class DeploymentNotifier:
    """Deployment notification handler"""
    
    def __init__(self):
        self.slack_webhook_url = self._get_webhook_url()
    
    def _get_webhook_url(self) -> str:
        """Get Slack webhook URL from environment"""
        import os
        return os.environ.get('SLACK_WEBHOOK_URL', '')
    
    def send_slack_notification(
        self,
        status: str,
        environment: str,
        version: str,
        details: Dict[str, Any] = None
    ) -> bool:
        """Send Slack notification"""
        if not self.slack_webhook_url:
            print("警告: 未配置SLACK_WEBHOOK_URL，跳过Slack通知")
            return False
        
        # Determine emoji and color based on status
        status_config = {
            'success': {'emoji': '✅', 'color': 'good'},
            'failure': {'emoji': '❌', 'color': 'danger'},
            'rollback': {'emoji': '🔄', 'color': 'warning'},
            'deployment': {'emoji': '🚀', 'color': '#1890FF'}
        }
        
        config = status_config.get(status, status_config['deployment'])
        
        # Build message payload
        payload = {
            'text': f'Deployment {status}',
            'blocks': [
                {
                    'type': 'section',
                    'text': {
                        'type': 'mrkdwn',
                        'text': f"{config['emoji']} *{status.upper()}*: {environment} environment"
                    }
                },
                {
                    'type': 'section',
                    'fields': [
                        {
                            'type': 'mrkdwn',
                            'text': f"*Environment:*\n{environment}"
                        },
                        {
                            'type': 'mrkdwn',
                            'text': f"*Version:*\n{version}"
                        }
                    ]
                },
                {
                    'type': 'section',
                    'fields': [
                        {
                            'type': 'mrkdwn',
                            'text': f"*Time:*\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        },
                        {
                            'type': 'mrkdwn',
                            'text': f"*Status:*\n{status.upper()}"
                        }
                    ]
                }
            ]
        }
        
        # Add details if provided
        if details:
            detail_text = '\n'.join([f'*{k}:* {v}' for k, v in details.items()])
            payload['blocks'].append({
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': detail_text
                }
            })
        
        try:
            response = requests.post(
                self.slack_webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"Slack通知发送成功: {status}")
                return True
            else:
                print(f"Slack通知发送失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"发送Slack通知时出错: {e}")
            return False
    
    def send_deployment_success(self, environment: str, version: str) -> bool:
        """Send deployment success notification"""
        return self.send_slack_notification(
            status='success',
            environment=environment,
            version=version,
            details={
                'Service': 'YL-AR-DGN',
                'Environment': environment
            }
        )
    
    def send_deployment_failure(self, environment: str, version: str, error: str) -> bool:
        """Send deployment failure notification"""
        return self.send_slack_notification(
            status='failure',
            environment=environment,
            version=version,
            details={
                'Error': error[:100] if error else 'Unknown error'
            }
        )
    
    def send_rollback_notification(self, environment: str, version: str) -> bool:
        """Send rollback notification"""
        return self.send_slack_notification(
            status='rollback',
            environment=environment,
            version=version
        )


def main():
    """Main entry point"""
    if len(sys.argv) < 3:
        print("用法: python notify_deployment.py <environment> <version> [status]")
        sys.exit(1)
    
    environment = sys.argv[1]
    version = sys.argv[2]
    status = sys.argv[3] if len(sys.argv) > 3 else 'success'
    
    notifier = DeploymentNotifier()
    
    if status == 'success':
        success = notifier.send_deployment_success(environment, version)
    elif status == 'failure':
        error = sys.argv[4] if len(sys.argv) > 4 else 'Unknown'
        success = notifier.send_deployment_failure(environment, version, error)
    elif status == 'rollback':
        success = notifier.send_rollback_notification(environment, version)
    else:
        success = notifier.send_slack_notification(status, environment, version)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

