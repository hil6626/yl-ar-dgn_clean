/**
 * 【文件功能】Service Worker - 浏览器推送通知后台处理
 * 处理后台推送消息、通知显示和交互
 * 
 * 【作者信息】
 * 作者: AI Assistant
 * 创建时间: 2026-02-08
 * 最后更新: 2026-02-08
 * 
 * 【版本历史】
 * - v1.0.0 (2026-02-08): 初始版本，实现推送通知后台处理
 */

const CACHE_NAME = 'yl-monitor-notifications-v1';
const STATIC_ASSETS = [
    '/static/images/logo.png',
    '/static/images/info.png',
    '/static/images/warning.png',
    '/static/images/error.png',
    '/static/images/critical.png'
];

/**
 * 【安装事件】Service Worker安装
 * 预缓存静态资源
 */
self.addEventListener('install', (event) => {
    console.log('[Service Worker] 安装中...');
    
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('[Service Worker] 缓存静态资源');
                return cache.addAll(STATIC_ASSETS);
            })
            .then(() => {
                console.log('[Service Worker] 安装完成');
                return self.skipWaiting();
            })
            .catch((error) => {
                console.error('[Service Worker] 安装失败:', error);
            })
    );
});

/**
 * 【激活事件】Service Worker激活
 * 清理旧缓存
 */
self.addEventListener('activate', (event) => {
    console.log('[Service Worker] 激活中...');
    
    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames
                        .filter((name) => name !== CACHE_NAME)
                        .map((name) => {
                            console.log('[Service Worker] 删除旧缓存:', name);
                            return caches.delete(name);
                        })
                );
            })
            .then(() => {
                console.log('[Service Worker] 激活完成');
                return self.clients.claim();
            })
    );
});

/**
 * 【推送事件】接收服务器推送消息
 * 显示通知
 */
self.addEventListener('push', (event) => {
    console.log('[Service Worker] 收到推送消息');
    
    if (!event.data) {
        console.warn('[Service Worker] 推送消息无数据');
        return;
    }

    try {
        const data = event.data.json();
        console.log('[Service Worker] 推送数据:', data);
        
        const title = data.title || 'YL-Monitor 通知';
        const options = {
            body: data.body || '',
            icon: data.icon || '/static/images/logo.png',
            badge: data.badge || '/static/images/badge.png',
            tag: data.tag || `push-${Date.now()}`,
            requireInteraction: data.requireInteraction || false,
            silent: data.silent || false,
            timestamp: data.timestamp || Date.now(),
            data: data.data || {},
            actions: data.actions || []
        };

        // 根据类型设置默认操作
        if (data.type === 'alert' && !options.actions.length) {
            options.actions = [
                { action: 'view', title: '查看详情' },
                { action: 'acknowledge', title: '确认' }
            ];
        }

        event.waitUntil(
            self.registration.showNotification(title, options)
                .then(() => {
                    console.log('[Service Worker] 通知已显示');
                    // 通知所有客户端
                    return self.clients.matchAll({ type: 'window' });
                })
                .then((clients) => {
                    clients.forEach((client) => {
                        client.postMessage({
                            type: 'NOTIFICATION_SHOWN',
                            data: { title, options }
                        });
                    });
                })
                .catch((error) => {
                    console.error('[Service Worker] 显示通知失败:', error);
                })
        );
    } catch (error) {
        console.error('[Service Worker] 处理推送消息失败:', error);
        
        // 显示默认通知
        event.waitUntil(
            self.registration.showNotification('YL-Monitor', {
                body: '收到新消息',
                icon: '/static/images/logo.png',
                tag: 'default-notification'
            })
        );
    }
});

/**
 * 【通知点击事件】处理通知点击
 */
self.addEventListener('notificationclick', (event) => {
    console.log('[Service Worker] 通知被点击:', event.notification.tag);
    
    event.notification.close();
    
    const notification = event.notification;
    const action = event.action;
    const data = notification.data || {};
    
    // 处理不同操作
    if (action === 'view') {
        // 查看详情 - 打开相关页面
        event.waitUntil(
            self.clients.openWindow(data.url || '/alerts')
        );
    } else if (action === 'acknowledge') {
        // 确认告警 - 发送确认请求
        event.waitUntil(
            acknowledgeAlert(data.alertId)
                .then(() => {
                    // 通知所有客户端
                    return self.clients.matchAll({ type: 'window' });
                })
                .then((clients) => {
                    clients.forEach((client) => {
                        client.postMessage({
                            type: 'ALERT_ACKNOWLEDGED',
                            data: { alertId: data.alertId }
                        });
                    });
                })
        );
    } else {
        // 默认行为 - 打开应用
        event.waitUntil(
            self.clients.matchAll({ type: 'window', includeUncontrolled: true })
                .then((clientList) => {
                    if (clientList.length > 0) {
                        // 聚焦到已有窗口
                        const client = clientList[0];
                        client.focus();
                        // 发送消息到客户端
                        client.postMessage({
                            type: 'NOTIFICATION_CLICKED',
                            data: { 
                                tag: notification.tag,
                                alertId: data.alertId,
                                ruleId: data.ruleId
                            }
                        });
                    } else {
                        // 打开新窗口
                        return self.clients.openWindow(data.url || '/');
                    }
                })
        );
    }
});

/**
 * 【通知关闭事件】处理通知关闭
 */
self.addEventListener('notificationclose', (event) => {
    console.log('[Service Worker] 通知被关闭:', event.notification.tag);
    
    // 通知所有客户端
    event.waitUntil(
        self.clients.matchAll({ type: 'window' })
            .then((clients) => {
                clients.forEach((client) => {
                    client.postMessage({
                        type: 'NOTIFICATION_CLOSED',
                        data: { tag: event.notification.tag }
                    });
                });
            })
    );
});

/**
 * 【消息事件】接收客户端消息
 */
self.addEventListener('message', (event) => {
    console.log('[Service Worker] 收到客户端消息:', event.data);
    
    const { type, data } = event.data || {};
    
    switch (type) {
        case 'GET_STATUS':
            // 返回状态给客户端
            event.source.postMessage({
                type: 'STATUS_RESPONSE',
                data: {
                    serviceWorker: true,
                    pushSubscription: !!self.registration.pushManager
                }
            });
            break;
            
        case 'SHOW_NOTIFICATION':
            // 显示本地通知
            self.registration.showNotification(data.title, data.options)
                .then(() => {
                    event.source.postMessage({
                        type: 'NOTIFICATION_SHOWN_SUCCESS',
                        data: { title: data.title }
                    });
                })
                .catch((error) => {
                    event.source.postMessage({
                        type: 'NOTIFICATION_SHOWN_ERROR',
                        data: { error: error.message }
                    });
                });
            break;
            
        case 'CLOSE_NOTIFICATIONS':
            // 关闭指定标签的通知
            self.registration.getNotifications({ tag: data.tag })
                .then((notifications) => {
                    notifications.forEach((notification) => notification.close());
                });
            break;
            
        default:
            console.log('[Service Worker] 未知消息类型:', type);
    }
});

/**
 * 【同步事件】后台同步（用于离线支持）
 */
self.addEventListener('sync', (event) => {
    if (event.tag === 'acknowledge-alert') {
        event.waitUntil(syncAcknowledgeAlerts());
    }
});

/**
 * 【获取事件】拦截网络请求
 * 优先从缓存获取静态资源
 */
self.addEventListener('fetch', (event) => {
    // 只处理GET请求
    if (event.request.method !== 'GET') {
        return;
    }
    
    // 只处理静态资源
    const url = new URL(event.request.url);
    if (!url.pathname.startsWith('/static/')) {
        return;
    }
    
    event.respondWith(
        caches.match(event.request)
            .then((response) => {
                // 缓存命中，返回缓存
                if (response) {
                    return response;
                }
                
                // 缓存未命中，发起网络请求
                return fetch(event.request)
                    .then((response) => {
                        // 缓存新资源
                        if (response.status === 200) {
                            const responseClone = response.clone();
                            caches.open(CACHE_NAME)
                                .then((cache) => {
                                    cache.put(event.request, responseClone);
                                });
                        }
                        return response;
                    });
            })
            .catch(() => {
                // 网络失败，返回离线页面（如果有）
                console.warn('[Service Worker] 获取资源失败:', event.request.url);
            })
    );
});

/**
 * 【辅助函数】确认告警
 * 
 * @param {string} alertId - 告警ID
 * @returns {Promise}
 */
async function acknowledgeAlert(alertId) {
    if (!alertId) {
        return Promise.resolve();
    }
    
    try {
        const response = await fetch('/api/alerts/acknowledge', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ alert_id: alertId })
        });
        
        if (!response.ok) {
            throw new Error(`确认告警失败: ${response.status}`);
        }
        
        console.log('[Service Worker] 告警已确认:', alertId);
        return response.json();
    } catch (error) {
        console.error('[Service Worker] 确认告警失败:', error);
        // 存储到后台同步队列
        if ('sync' in self.registration) {
            await self.registration.sync.register('acknowledge-alert');
        }
        throw error;
    }
}

/**
 * 【辅助函数】同步确认告警队列
 */
async function syncAcknowledgeAlerts() {
    // 从IndexedDB获取待确认的告警列表
    // 这里简化处理，实际应该使用IndexedDB存储
    console.log('[Service Worker] 同步确认告警队列');
}

/**
 * 【辅助函数】检查通知权限
 * 
 * @returns {Promise<string>}
 */
async function checkNotificationPermission() {
    if (!('Notification' in self)) {
        return 'unsupported';
    }
    
    // 通过客户端检查权限
    const clients = await self.clients.matchAll({ type: 'window' });
    if (clients.length > 0) {
        // 向客户端发送权限检查请求
        clients[0].postMessage({ type: 'CHECK_PERMISSION' });
    }
    
    return 'unknown';
}

// Service Worker 启动日志
console.log('[Service Worker] 已加载，版本: 1.0.0');
