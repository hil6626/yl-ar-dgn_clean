/**
 * Dashboard页面测试
 * 测试Dashboard组件和功能
 * 版本: v1.0.0
 */

import { TestRunner, MockUtils, DOMTestUtils } from '../../static/js/utils/TestUtils.js';
import { RealtimeDataPanel } from '../../static/js/pages/dashboard/components/RealtimeDataPanel.js';
import { WebSocketManager } from '../../static/js/pages/dashboard/managers/WebSocketManager.js';

const runner = new TestRunner();

// 测试RealtimeDataPanel
runner.test('RealtimeDataPanel 初始化', async () => {
  const container = DOMTestUtils.createContainer();
  
  const panel = new RealtimeDataPanel({
    onMetricClick: () => {}
  });
  
  panel.init(container);
  
  runner.assertTrue(
    container.querySelector('.realtime-panel') !== null,
    '面板应该被渲染'
  );
  
  DOMTestUtils.cleanup();
});

runner.test('RealtimeDataPanel 指标更新', async () => {
  const container = DOMTestUtils.createContainer();
  
  const panel = new RealtimeDataPanel({
    onMetricClick: () => {}
  });
  
  panel.init(container);
  
  // 模拟指标数据
  const metrics = {
    cpu: 45.5,
    memory: 60.2,
    disk: 30.8,
    network: 100
  };
  
  panel.updateMetrics(metrics);
  
  // 验证指标显示
  const cpuValue = container.querySelector('[data-metric="cpu"] .metric-value');
  runner.assertTrue(
    cpuValue !== null,
    'CPU指标应该显示'
  );
  
  DOMTestUtils.cleanup();
});

// 测试WebSocketManager
runner.test('WebSocketManager 连接管理', async () => {
  const mockFetch = MockUtils.createMockFetch({
    'GET /api/v1/dashboard/metrics': {
      status: 200,
      json: { cpu: 50, memory: 60 }
    }
  });
  
  const manager = new WebSocketManager();
  
  // 模拟WebSocket
  const mockWS = {
    send: () => {},
    close: () => {},
    readyState: WebSocket.OPEN
  };
  
  manager.ws = mockWS;
  
  runner.assertTrue(
    manager.isConnected(),
    '应该显示为已连接'
  );
  
  mockFetch.restore();
});

runner.test('WebSocketManager 消息处理', async () => {
  const manager = new WebSocketManager();
  let receivedMessage = null;
  
  manager.on('metrics', (data) => {
    receivedMessage = data;
  });
  
  // 模拟收到消息
  manager.handleMessage(JSON.stringify({
    type: 'metrics',
    data: { cpu: 50 }
  }));
  
  runner.assertEqual(
    receivedMessage?.data?.cpu,
    50,
    '应该正确解析消息'
  );
});

// 运行测试
if (typeof window !== 'undefined') {
  runner.run();
}

export { runner };
