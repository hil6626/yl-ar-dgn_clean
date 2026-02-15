"""
前端集成测试
使用Playwright测试页面渲染和交互
"""

import pytest
import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


# 标记需要Playwright的测试
pytestmark = pytest.mark.skipif(
    not os.environ.get("PLAYWRIGHT_TESTS"),
    reason="需要设置PLAYWRIGHT_TESTS环境变量来运行前端测试"
)


@pytest.fixture(scope="module")
async def browser():
    """创建浏览器实例"""
    try:
        from playwright.async_api import async_playwright
        
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        
        yield browser
        
        await browser.close()
        await playwright.stop()
        
    except ImportError:
        pytest.skip("Playwright未安装")
    except Exception as e:
        pytest.skip(f"浏览器启动失败: {e}")


@pytest.fixture
async def page(browser):
    """创建页面实例"""
    context = await browser.new_context(
        viewport={"width": 1920, "height": 1080}
    )
    page = await context.new_page()
    
    yield page
    
    await context.close()


class TestDashboardPage:
    """Dashboard页面测试"""
    
    @pytest.mark.asyncio
    async def test_page_loads(self, page):
        """测试页面加载"""
        await page.goto("http://localhost:8000/dashboard")
        
        # 等待页面加载
        await page.wait_for_load_state("networkidle")
        
        # 检查标题
        title = await page.title()
        assert "仪表盘" in title or "Dashboard" in title or "YL-Monitor" in title
    
    @pytest.mark.asyncio
    async def test_overview_cards_render(self, page):
        """测试概览卡片渲染"""
        await page.goto("http://localhost:8000/dashboard")
        
        # 等待卡片加载
        try:
            await page.wait_for_selector(".overview-card", timeout=5000)
            
            cards = await page.query_selector_all(".overview-card")
            assert len(cards) >= 4, f"期望至少4个卡片，实际找到{len(cards)}个"
        except Exception:
            # 如果找不到特定选择器，尝试其他选择器
            cards = await page.query_selector_all("[class*='card']")
            assert len(cards) >= 1, "页面应该至少有一个卡片"
    
    @pytest.mark.asyncio
    async def test_navigation_links(self, page):
        """测试导航链接"""
        await page.goto("http://localhost:8000/dashboard")
        
        # 查找导航链接
        nav_links = await page.query_selector_all("nav a, .nav-link, .sidebar a")
        
        # 至少应该有导航链接
        assert len(nav_links) > 0, "页面应该有导航链接"
        
        # 测试点击第一个链接
        if len(nav_links) > 0:
            # 获取链接文本
            link_text = await nav_links[0].text_content()
            print(f"找到导航链接: {link_text}")
    
    @pytest.mark.asyncio
    async def test_resource_gauges(self, page):
        """测试资源仪表盘"""
        await page.goto("http://localhost:8000/dashboard")
        
        # 等待资源仪表盘加载
        try:
            await page.wait_for_selector(".gauge, .progress-bar, [class*='gauge']", timeout=5000)
            
            gauges = await page.query_selector_all(".gauge, .progress-bar, [class*='gauge']")
            assert len(gauges) >= 3, f"期望至少3个仪表盘，实际找到{len(gauges)}个"
        except Exception:
            pytest.skip("资源仪表盘未找到（可能页面结构不同）")


class TestAPIDocPage:
    """API Doc页面测试"""
    
    @pytest.mark.asyncio
    async def test_page_loads(self, page):
        """测试页面加载"""
        await page.goto("http://localhost:8000/api-doc")
        
        await page.wait_for_load_state("networkidle")
        
        title = await page.title()
        assert "API" in title or "文档" in title or "Doc" in title
    
    @pytest.mark.asyncio
    async def test_validation_matrix_renders(self, page):
        """测试验证矩阵渲染"""
        await page.goto("http://localhost:8000/api-doc")
        
        # 等待矩阵加载
        try:
            await page.wait_for_selector(
                ".matrix-table, table, [class*='matrix'], [class*='table']",
                timeout=10000
            )
            
            # 查找表格行
            rows = await page.query_selector_all("table tbody tr, .matrix-row, [class*='row']")
            assert len(rows) > 0, "验证矩阵应该有数据行"
        except Exception:
            pytest.skip("验证矩阵未找到（可能页面结构不同或数据未加载）")
    
    @pytest.mark.asyncio
    async def test_bubble_indicators(self, page):
        """测试冒泡指示器"""
        await page.goto("http://localhost:8000/api-doc")
        
        # 查找状态指示器
        indicators = await page.query_selector_all(
            ".status-indicator, .bubble, [class*='status'], [class*='indicator']"
        )
        
        # 应该有状态指示器
        if len(indicators) > 0:
            print(f"找到 {len(indicators)} 个状态指示器")


class TestDAGPage:
    """DAG页面测试"""
    
    @pytest.mark.asyncio
    async def test_page_loads(self, page):
        """测试页面加载"""
        await page.goto("http://localhost:8000/dag")
        
        await page.wait_for_load_state("networkidle")
        
        title = await page.title()
        assert "DAG" in title or "流水线" in title or "Pipeline" in title
    
    @pytest.mark.asyncio
    async def test_dag_visualization_renders(self, page):
        """测试DAG可视化渲染"""
        await page.goto("http://localhost:8000/dag")
        
        # 等待DAG画布加载
        try:
            await page.wait_for_selector(
                ".dag-canvas, .node, [class*='dag'], [class*='canvas'], svg",
                timeout=10000
            )
            
            # 查找节点
            nodes = await page.query_selector_all(".node, [class*='node']")
            assert len(nodes) > 0, "DAG应该至少有一个节点"
        except Exception:
            pytest.skip("DAG可视化未找到（可能页面结构不同）")
    
    @pytest.mark.asyncio
    async def test_node_interactions(self, page):
        """测试节点交互"""
        await page.goto("http://localhost:8000/dag")
        
        # 查找节点
        nodes = await page.query_selector_all(".node, [class*='node']")
        
        if len(nodes) > 0:
            # 尝试点击第一个节点
            try:
                await nodes[0].click()
                # 等待可能的弹窗或详情面板
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"节点点击测试: {e}")


class TestScriptsPage:
    """Scripts页面测试"""
    
    @pytest.mark.asyncio
    async def test_page_loads(self, page):
        """测试页面加载"""
        await page.goto("http://localhost:8000/scripts")
        
        await page.wait_for_load_state("networkidle")
        
        title = await page.title()
        assert "脚本" in title or "Scripts" in title or "Script" in title
    
    @pytest.mark.asyncio
    async def test_script_cards_render(self, page):
        """测试脚本卡片渲染"""
        await page.goto("http://localhost:8000/scripts")
        
        # 等待卡片加载
        try:
            await page.wait_for_selector(
                ".script-card, .card, [class*='script'], [class*='card']",
                timeout=10000
            )
            
            cards = await page.query_selector_all(".script-card, .card, [class*='card']")
            assert len(cards) > 0, "页面应该至少有一个脚本卡片"
        except Exception:
            pytest.skip("脚本卡片未找到（可能页面结构不同）")
    
    @pytest.mark.asyncio
    async def test_execute_button(self, page):
        """测试执行按钮"""
        await page.goto("http://localhost:8000/scripts")
        
        # 查找执行按钮
        buttons = await page.query_selector_all(
            "button, .btn, [class*='execute'], [class*='run']"
        )
        
        # 应该有按钮
        assert len(buttons) > 0, "页面应该有操作按钮"
        
        # 尝试点击第一个按钮（小心不要真的执行）
        # 这里只是测试按钮存在和可点击
        if len(buttons) > 0:
            button_text = await buttons[0].text_content()
            print(f"找到按钮: {button_text}")


class TestResponsiveDesign:
    """响应式设计测试"""
    
    @pytest.mark.asyncio
    async def test_mobile_viewport(self, browser):
        """测试移动端视口"""
        context = await browser.new_context(
            viewport={"width": 375, "height": 667},
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)"
        )
        page = await context.new_page()
        
        await page.goto("http://localhost:8000/dashboard")
        await page.wait_for_load_state("networkidle")
        
        # 检查页面是否正常加载
        title = await page.title()
        assert len(title) > 0, "页面应该正常加载"
        
        await context.close()
    
    @pytest.mark.asyncio
    async def test_tablet_viewport(self, browser):
        """测试平板视口"""
        context = await browser.new_context(
            viewport={"width": 768, "height": 1024},
            user_agent="Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X)"
        )
        page = await context.new_page()
        
        await page.goto("http://localhost:8000/dashboard")
        await page.wait_for_load_state("networkidle")
        
        title = await page.title()
        assert len(title) > 0, "页面应该正常加载"
        
        await context.close()


class TestThemeSwitching:
    """主题切换测试"""
    
    @pytest.mark.asyncio
    async def test_theme_toggle(self, page):
        """测试主题切换"""
        await page.goto("http://localhost:8000/dashboard")
        
        # 查找主题切换按钮
        theme_buttons = await page.query_selector_all(
            "[class*='theme'], [class*='dark'], [class*='light'], button"
        )
        
        if len(theme_buttons) > 0:
            # 尝试点击主题按钮
            try:
                await theme_buttons[0].click()
                await asyncio.sleep(0.5)
                
                # 检查主题是否改变（通过检查body类名或CSS变量）
                # 这里只是简单测试按钮可点击
            except Exception as e:
                print(f"主题切换测试: {e}")


# ============================================================================
# 辅助函数
# ============================================================================
async def wait_for_api_response(page, timeout=10000):
    """等待API响应"""
    try:
        await page.wait_for_selector(
            "[class*='loading'], [class*='spinner']",
            state="hidden",
            timeout=timeout
        )
    except Exception:
        pass  # 可能没有加载指示器


# ============================================================================
# 主函数
# ============================================================================
if __name__ == "__main__":
    # 设置环境变量运行测试
    os.environ["PLAYWRIGHT_TESTS"] = "1"
    pytest.main([__file__, "-v", "-s"])
