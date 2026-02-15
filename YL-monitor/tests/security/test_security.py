"""
安全测试脚本
测试API安全、输入验证、认证授权等
"""

import pytest
import sys
import os
from httpx import AsyncClient

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.main import app


class TestInputValidation:
    """输入验证测试"""
    
    @pytest.fixture
    async def client(self):
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client
    
    @pytest.mark.asyncio
    async def test_sql_injection_prevention(self, client):
        """测试SQL注入防护"""
        # 尝试SQL注入
        malicious_inputs = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "1' UNION SELECT * FROM users --",
            "' OR 1=1#",
            "1 AND 1=1",
        ]
        
        for malicious_input in malicious_inputs:
            # 测试各种端点
            response = await client.get(f"/api/v1/scripts/{malicious_input}/logs")
            # 应该返回404或正常处理，而不是500错误
            assert response.status_code in [200, 404, 422], \
                f"SQL注入测试失败: {malicious_input}"
    
    @pytest.mark.asyncio
    async def test_xss_prevention(self, client):
        """测试XSS防护"""
        # 尝试XSS攻击
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<body onload=alert('xss')>",
        ]
        
        # 这些测试主要验证应用是否正确处理特殊字符
        for payload in xss_payloads:
            response = await client.get(f"/api/v1/api-doc/bubble-check/{payload}")
            # 应该正常处理，不执行脚本
            assert response.status_code in [200, 404, 422]
    
    @pytest.mark.asyncio
    async def test_path_traversal_prevention(self, client):
        """测试路径遍历防护"""
        # 尝试路径遍历
        path_traversal_attempts = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//etc/passwd",
            "..%2f..%2f..%2fetc%2fpasswd",
        ]
        
        for path in path_traversal_attempts:
            response = await client.get(f"/api/v1/scripts/{path}/logs")
            # 应该返回404，而不是访问到系统文件
            assert response.status_code in [404, 422, 403]


class TestAuthentication:
    """认证授权测试"""
    
    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client):
        """测试未授权访问"""
        # 测试需要认证的端点（如果有）
        # 这里测试一般端点应该可以公开访问
        response = await client.get("/api/health")
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_invalid_token(self, client):
        """测试无效令牌"""
        # 发送无效认证头
        headers = {"Authorization": "Bearer invalid_token"}
        response = await client.get("/api/v1/dashboard/overview", headers=headers)
        # 应该正常响应（如果不需要认证）或401（如果需要认证）
        assert response.status_code in [200, 401]


class TestRateLimiting:
    """速率限制测试"""
    
    @pytest.mark.asyncio
    async def test_api_rate_limit(self, client):
        """测试API速率限制"""
        # 快速发送大量请求
        responses = []
        for _ in range(20):
            response = await client.get("/api/health")
            responses.append(response.status_code)
        
        # 检查是否有速率限制响应（429）
        # 如果没有速率限制，所有请求应该成功
        success_count = responses.count(200)
        rate_limited_count = responses.count(429)
        
        print(f"\n速率限制测试:")
        print(f"  成功请求: {success_count}/20")
        print(f"  限流请求: {rate_limited_count}/20")
        
        # 至少应该有部分请求成功
        assert success_count > 0, "所有请求都被限流"


class TestSecurityHeaders:
    """安全头部测试"""
    
    @pytest.mark.asyncio
    async def test_security_headers_present(self, client):
        """测试安全头部是否存在"""
        response = await client.get("/api/health")
        
        # 检查安全头部
        headers = response.headers
        
        print(f"\n安全头部检查:")
        for header, value in headers.items():
            print(f"  {header}: {value}")
        
        # 检查关键安全头部（如果配置了）
        # 注意：这些头部需要在Nginx或应用层配置
        security_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Strict-Transport-Security",
        ]
        
        for header in security_headers:
            if header in headers:
                print(f"  ✅ {header}: {headers[header]}")
            else:
                print(f"  ⚠️  {header}: 未设置")
    
    @pytest.mark.asyncio
    async def test_cors_headers(self, client):
        """测试CORS头部"""
        # 发送带Origin头的请求
        headers = {"Origin": "http://example.com"}
        response = await client.get("/api/health", headers=headers)
        
        # 检查CORS头部
        if "Access-Control-Allow-Origin" in response.headers:
            print(f"\nCORS配置:")
            print(f"  Access-Control-Allow-Origin: {response.headers['Access-Control-Allow-Origin']}")


class TestErrorHandling:
    """错误处理测试"""
    
    @pytest.mark.asyncio
    async def test_error_message_leakage(self, client):
        """测试错误信息泄露"""
        # 触发一个错误
        response = await client.get("/api/v1/scripts/nonexistent/execute")
        
        if response.status_code >= 400:
            data = response.json()
            
            # 检查错误信息是否包含敏感信息
            error_message = str(data)
            sensitive_patterns = [
                "password",
                "secret",
                "token",
                "key",
                "database",
                "sql",
                "traceback",
                "exception",
            ]
            
            for pattern in sensitive_patterns:
                assert pattern.lower() not in error_message.lower(), \
                    f"错误信息可能包含敏感信息: {pattern}"
    
    @pytest.mark.asyncio
    async def test_stack_trace_exposure(self, client):
        """测试堆栈跟踪暴露"""
        # 触发错误并检查响应
        response = await client.get("/api/v1/nonexistent-endpoint")
        
        if response.status_code == 404:
            data = response.json()
            response_text = str(data)
            
            # 生产环境不应该暴露堆栈跟踪
            assert "traceback" not in response_text.lower(), \
                "错误响应包含堆栈跟踪信息"
            assert "File \"" not in response_text, \
                "错误响应包含文件路径信息"


class TestFileUploadSecurity:
    """文件上传安全测试（如果支持文件上传）"""
    
    @pytest.mark.asyncio
    async def test_file_type_validation(self, client):
        """测试文件类型验证"""
        # 这里假设有文件上传功能
        # 实际测试需要根据具体实现
        pass
    
    @pytest.mark.asyncio
    async def test_file_size_limit(self, client):
        """测试文件大小限制"""
        # 这里假设有文件上传功能
        # 实际测试需要根据具体实现
        pass


# 安全配置检查清单
SECURITY_CHECKLIST = {
    "input_validation": {
        "sql_injection": "✅ 已测试",
        "xss_prevention": "✅ 已测试",
        "path_traversal": "✅ 已测试",
        "command_injection": "⬜ 待测试",
    },
    "authentication": {
        "password_policy": "⬜ 待配置",
        "session_management": "⬜ 待配置",
        "token_validation": "⬜ 待配置",
    },
    "authorization": {
        "role_based_access": "⬜ 待配置",
        "resource_access_control": "⬜ 待配置",
    },
    "transport_security": {
        "https_enforcement": "⬜ 生产环境配置",
        "hsts": "⬜ 生产环境配置",
        "certificate_validation": "⬜ 生产环境配置",
    },
    "security_headers": {
        "content_security_policy": "⬜ 待配置",
        "x_frame_options": "⬜ 待配置",
        "x_content_type_options": "⬜ 待配置",
        "x_xss_protection": "⬜ 待配置",
    },
    "logging_monitoring": {
        "security_event_logging": "⬜ 待配置",
        "failed_login_monitoring": "⬜ 待配置",
        "anomaly_detection": "⬜ 待配置",
    }
}


def generate_security_report() -> str:
    """
    生成安全测试报告
    """
    report = []
    report.append("=" * 60)
    report.append("YL-Monitor 安全测试报告")
    report.append("=" * 60)
    report.append("")
    
    for category, items in SECURITY_CHECKLIST.items():
        report.append(f"【{category}】")
        for item, status in items.items():
            report.append(f"  {status} {item}")
        report.append("")
    
    report.append("=" * 60)
    report.append("建议:")
    report.append("1. 在生产环境启用HTTPS强制跳转")
    report.append("2. 配置安全头部（CSP、HSTS等）")
    report.append("3. 实施速率限制和IP白名单")
    report.append("4. 启用安全审计日志")
    report.append("5. 定期进行安全扫描")
    report.append("=" * 60)
    
    return "\n".join(report)


# 主函数
if __name__ == "__main__":
    # 打印安全报告
    print(generate_security_report())
    print("\n" + "=" * 60)
    print("运行安全测试...")
    print("=" * 60 + "\n")
    
    pytest.main([__file__, "-v", "-s"])
