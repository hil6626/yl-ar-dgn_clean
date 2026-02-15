/**
 * API数据管理器
 * 拆分自: page-api-doc.js
 * 版本: v1.0.0
 */

export class APIDataManager {
  constructor(page) {
    this.page = page;
    this.apiBaseUrl = '/api/v1';
  }

  /**
   * 加载API数据
   * @returns {Promise<Array>}
   */
  async load() {
    try {
      const response = await fetch(`${this.apiBaseUrl}/api-doc/endpoints`);
      if (!response.ok) throw new Error('获取API数据失败');
      
      return await response.json();
    } catch (error) {
      console.error('[APIDataManager] 获取API数据失败:', error);
      return this.getSampleData();
    }
  }

  /**
   * 获取示例API数据
   * @returns {Array}
   */
  getSampleData() {
    return [
      {
        module: '用户管理',
        icon: '👤',
        expanded: true,
        endpoints: [
          {
            id: 'user-list',
            method: 'GET',
            path: '/api/v1/users',
            name: '获取用户列表',
            description: '获取所有用户的列表，支持分页和筛选',
            params: [
              { name: 'page', type: 'integer', required: false, description: '页码，默认1' },
              { name: 'size', type: 'integer', required: false, description: '每页数量，默认20' }
            ],
            response: {
              status: 200,
              example: {
                code: 0,
                data: {
                  items: [{ id: 1, name: '张三', email: 'zhangsan@example.com' }],
                  total: 100,
                  page: 1,
                  size: 20
                },
                message: 'success'
              }
            }
          },
          {
            id: 'user-create',
            method: 'POST',
            path: '/api/v1/users',
            name: '创建用户',
            description: '创建新用户账号',
            params: [
              { name: 'name', type: 'string', required: true, description: '用户姓名' },
              { name: 'email', type: 'string', required: true, description: '邮箱地址' },
              { name: 'role', type: 'string', required: false, description: '用户角色' }
            ],
            body: {
              name: 'John Doe',
              email: 'john@example.com',
              role: 'user'
            },
            response: {
              status: 201,
              example: {
                code: 0,
                data: { id: 1, name: 'John Doe', email: 'john@example.com' },
                message: '创建成功'
              }
            }
          }
        ]
      },
      {
        module: '告警管理',
        icon: '🚨',
        expanded: false,
        endpoints: [
          {
            id: 'alert-list',
            method: 'GET',
            path: '/api/v1/alerts',
            name: '获取告警列表',
            description: '获取系统告警列表',
            params: [
              { name: 'level', type: 'string', required: false, description: '告警级别' },
              { name: 'status', type: 'string', required: false, description: '告警状态' }
            ],
            response: {
              status: 200,
              example: {
                code: 0,
                data: {
                  items: [{ id: 1, level: 'critical', message: 'CPU使用率过高' }],
                  total: 10
                }
              }
            }
          },
          {
            id: 'alert-ack',
            method: 'POST',
            path: '/api/v1/alerts/{id}/acknowledge',
            name: '确认告警',
            description: '确认指定告警',
            params: [
              { name: 'id', type: 'string', required: true, description: '告警ID', in: 'path' }
            ],
            response: {
              status: 200,
              example: { code: 0, message: '确认成功' }
            }
          }
        ]
      },
      {
        module: '系统监控',
        icon: '📊',
        expanded: false,
        endpoints: [
          {
            id: 'metrics',
            method: 'GET',
            path: '/api/v1/metrics',
            name: '获取系统指标',
            description: '获取系统性能指标',
            params: [],
            response: {
              status: 200,
              example: {
                code: 0,
                data: {
                  cpu: 45.2,
                  memory: 67.8,
                  disk: 82.1
                }
              }
            }
          }
        ]
      }
    ];
  }

  /**
   * 导出API文档
   * @param {Array} apiData - API数据
   */
  export(apiData) {
    const doc = {
      title: 'YL-Monitor API文档',
      version: 'v1.0.0',
      generatedAt: new Date().toISOString(),
      modules: apiData
    };

    const blob = new Blob([JSON.stringify(doc, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'yl-monitor-api-doc.json';
    a.click();
    URL.revokeObjectURL(url);
  }
}
