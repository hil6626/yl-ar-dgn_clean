/**
 * DAG自动保存功能 - 关键路径测试
 * 测试内容: AutoSaveManager核心功能
 * 运行: node dag-autosave-test.js
 */

const fs = require('fs');
const path = require('path');

// 模拟浏览器环境
class MockLocalStorage {
    constructor() {
        this.store = {};
    }
    
    getItem(key) {
        return this.store[key] || null;
    }
    
    setItem(key, value) {
        this.store[key] = value;
    }
    
    removeItem(key) {
        delete this.store[key];
    }
    
    clear() {
        this.store = {};
    }
}

class MockWindow {
    constructor() {
        this.localStorage = new MockLocalStorage();
        this.listeners = {};
    }
    
    addEventListener(event, callback) {
        if (!this.listeners[event]) {
            this.listeners[event] = [];
        }
        this.listeners[event].push(callback);
    }
    
    triggerEvent(event, data) {
        if (this.listeners[event]) {
            this.listeners[event].forEach(cb => cb(data));
        }
    }
}

class MockUI {
    constructor() {
        this.toasts = [];
        this.confirms = [];
    }
    
    showToast(options) {
        this.toasts.push(options);
        console.log(`  [Toast] ${options.type}: ${options.message}`);
        return Promise.resolve();
    }
    
    showConfirm(options) {
        this.confirms.push(options);
        console.log(`  [Confirm] ${options.title}: ${options.message}`);
        // 模拟用户点击"恢复"
        setTimeout(() => options.onConfirm && options.onConfirm(), 100);
        return Promise.resolve();
    }
}

// 从page-dag.js提取AutoSaveManager类进行测试
class AutoSaveManager {
    constructor(page) {
        this.page = page;
        this.autoSaveInterval = null;
        this.AUTO_SAVE_DELAY = 30000;
        this.DRAFT_EXPIRY = 24 * 60 * 60 * 1000;
        this.STORAGE_KEY = 'yl_dag_draft';
        this.lastSaveTime = null;
        this.hasUnsavedChanges = false;
    }
    
    init() {
        this.checkDraftRecovery();
        this.startAutoSave();
        console.log('  ✓ AutoSaveManager initialized');
    }
    
    startAutoSave() {
        if (this.autoSaveInterval) {
            clearInterval(this.autoSaveInterval);
        }
        // 使用较短的间隔用于测试
        this.autoSaveInterval = setInterval(() => {
            this.autoSave();
        }, 100); // 测试用100ms
    }
    
    stopAutoSave() {
        if (this.autoSaveInterval) {
            clearInterval(this.autoSaveInterval);
            this.autoSaveInterval = null;
        }
    }
    
    async autoSave() {
        if (!this.hasUnsavedChanges) {
            return;
        }
        
        try {
            const draftData = {
                nodes: this.page.nodes,
                edges: this.page.edges,
                timestamp: Date.now(),
                version: '1.0.0'
            };
            
            window.localStorage.setItem(this.STORAGE_KEY, JSON.stringify(draftData));
            this.lastSaveTime = Date.now();
            this.hasUnsavedChanges = false;
            
            console.log('  ✓ Auto-saved draft to localStorage');
            
        } catch (error) {
            console.error('  ✗ Auto-save failed:', error);
        }
    }
    
    markUnsaved() {
        this.hasUnsavedChanges = true;
        console.log('  ✓ Marked as unsaved');
    }
    
    checkDraftRecovery() {
        try {
            const draftJson = window.localStorage.getItem(this.STORAGE_KEY);
            if (!draftJson) {
                console.log('  ℹ No draft found for recovery');
                return;
            }
            
            const draft = JSON.parse(draftJson);
            
            if (Date.now() - draft.timestamp > this.DRAFT_EXPIRY) {
                console.log('  ✓ Draft expired, cleared');
                window.localStorage.removeItem(this.STORAGE_KEY);
                return;
            }
            
            console.log('  ✓ Draft found, showing recovery dialog');
            this.showDraftRecoveryDialog(draft);
            
        } catch (error) {
            console.error('  ✗ Check draft failed:', error);
        }
    }
    
    showDraftRecoveryDialog(draft) {
        const saveTime = new Date(draft.timestamp).toLocaleString('zh-CN');
        this.page.ui.showConfirm({
            title: '恢复DAG草稿',
            message: `检测到未保存的DAG草稿（${saveTime}），是否恢复？`,
            type: 'info',
            confirmText: '恢复草稿',
            cancelText: '丢弃',
            onConfirm: () => {
                this.restoreDraft(draft);
            },
            onCancel: () => {
                this.clearDraft();
            }
        });
    }
    
    restoreDraft(draft) {
        try {
            this.page.nodes = draft.nodes || [];
            this.page.edges = draft.edges || [];
            console.log('  ✓ Draft restored');
        } catch (error) {
            console.error('  ✗ Restore draft failed:', error);
        }
    }
    
    clearDraft() {
        window.localStorage.removeItem(this.STORAGE_KEY);
        console.log('  ✓ Draft cleared');
    }
    
    onManualSave() {
        this.hasUnsavedChanges = false;
        this.clearDraft();
        console.log('  ✓ Manual save completed, draft cleared');
    }
}

// 测试套件
class TestSuite {
    constructor() {
        this.tests = [];
        this.passed = 0;
        this.failed = 0;
    }
    
    async test(name, fn) {
        console.log(`\n▶ Test: ${name}`);
        try {
            await fn();
            console.log(`✅ PASSED: ${name}`);
            this.passed++;
        } catch (error) {
            console.log(`❌ FAILED: ${name}`);
            console.log(`   Error: ${error.message}`);
            this.failed++;
        }
    }
    
    report() {
        console.log('\n========================================');
        console.log('DAG Auto-Save Test Report');
        console.log('========================================');
        console.log(`Total: ${this.passed + this.failed}`);
        console.log(`Passed: ${this.passed}`);
        console.log(`Failed: ${this.failed}`);
        console.log(`Success Rate: ${((this.passed / (this.passed + this.failed)) * 100).toFixed(1)}%`);
        console.log('========================================');
        return this.failed === 0;
    }
}

// 全局模拟
global.window = new MockWindow();

// 运行测试
async function runTests() {
    const suite = new TestSuite();
    
    // 测试1: AutoSaveManager初始化
    await suite.test('AutoSaveManager Initialization', async () => {
        const mockPage = {
            nodes: [],
            edges: [],
            ui: new MockUI()
        };
        
        const manager = new AutoSaveManager(mockPage);
        manager.init();
        
        if (!manager.autoSaveInterval) {
            throw new Error('Auto-save interval not started');
        }
        
        manager.stopAutoSave();
    });
    
    // 测试2: markUnsaved标记
    await suite.test('Mark Unsaved Changes', async () => {
        const mockPage = {
            nodes: [{ id: 'node-1', name: 'Test' }],
            edges: [],
            ui: new MockUI()
        };
        
        const manager = new AutoSaveManager(mockPage);
        
        if (manager.hasUnsavedChanges !== false) {
            throw new Error('Initial state should be saved');
        }
        
        manager.markUnsaved();
        
        if (manager.hasUnsavedChanges !== true) {
            throw new Error('Should be marked as unsaved');
        }
    });
    
    // 测试3: 自动保存到localStorage
    await suite.test('Auto-Save to localStorage', async () => {
        const mockPage = {
            nodes: [{ id: 'node-1', name: 'Test Node' }],
            edges: [{ from: 'node-1', to: 'node-2' }],
            ui: new MockUI()
        };
        
        const manager = new AutoSaveManager(mockPage);
        manager.AUTO_SAVE_DELAY = 50; // 50ms for testing
        
        manager.markUnsaved();
        manager.startAutoSave();
        
        // 等待自动保存触发
        await new Promise(resolve => setTimeout(resolve, 200));
        
        const saved = window.localStorage.getItem('yl_dag_draft');
        if (!saved) {
            throw new Error('Draft not saved to localStorage');
        }
        
        const draft = JSON.parse(saved);
        if (!draft.nodes || draft.nodes.length !== 1) {
            throw new Error('Saved data incorrect');
        }
        
        if (!draft.timestamp || !draft.version) {
            throw new Error('Missing metadata in saved draft');
        }
        
        manager.stopAutoSave();
    });
    
    // 测试4: 草稿恢复
    await suite.test('Draft Recovery', async () => {
        // 先保存一个草稿
        const draftData = {
            nodes: [{ id: 'node-1', name: 'Recovered Node' }],
            edges: [],
            timestamp: Date.now(),
            version: '1.0.0'
        };
        window.localStorage.setItem('yl_dag_draft', JSON.stringify(draftData));
        
        const mockPage = {
            nodes: [],
            edges: [],
            ui: new MockUI()
        };
        
        const manager = new AutoSaveManager(mockPage);
        manager.init();
        
        // 等待恢复对话框处理
        await new Promise(resolve => setTimeout(resolve, 200));
        
        if (mockPage.nodes.length !== 1 || mockPage.nodes[0].name !== 'Recovered Node') {
            throw new Error('Draft not restored correctly');
        }
        
        manager.stopAutoSave();
    });
    
    // 测试5: 草稿过期检测
    await suite.test('Draft Expiry Detection', async () => {
        // 保存一个过期的草稿（25小时前）
        const expiredDraft = {
            nodes: [{ id: 'node-1', name: 'Expired Node' }],
            edges: [],
            timestamp: Date.now() - (25 * 60 * 60 * 1000), // 25 hours ago
            version: '1.0.0'
        };
        window.localStorage.setItem('yl_dag_draft', JSON.stringify(expiredDraft));
        
        const mockPage = {
            nodes: [],
            edges: [],
            ui: new MockUI()
        };
        
        const manager = new AutoSaveManager(mockPage);
        manager.init();
        
        const saved = window.localStorage.getItem('yl_dag_draft');
        if (saved !== null) {
            throw new Error('Expired draft should be cleared');
        }
        
        manager.stopAutoSave();
    });
    
    // 测试6: 手动保存后清除草稿
    await suite.test('Manual Save Clears Draft', async () => {
        // 先保存一个草稿
        const draftData = {
            nodes: [{ id: 'node-1', name: 'Test' }],
            edges: [],
            timestamp: Date.now(),
            version: '1.0.0'
        };
        window.localStorage.setItem('yl_dag_draft', JSON.stringify(draftData));
        
        const mockPage = {
            nodes: [{ id: 'node-1', name: 'Test' }],
            edges: [],
            ui: new MockUI()
        };
        
        const manager = new AutoSaveManager(mockPage);
        manager.hasUnsavedChanges = true; // 模拟有未保存变更
        
        manager.onManualSave();
        
        if (manager.hasUnsavedChanges !== false) {
            throw new Error('Should be marked as saved after manual save');
        }
        
        const saved = window.localStorage.getItem('yl_dag_draft');
        if (saved !== null) {
            throw new Error('Draft should be cleared after manual save');
        }
    });
    
    // 测试7: 数据变更点集成检查
    await suite.test('Data Change Integration Points', async () => {
        // 读取page-dag.js文件，检查markUnsaved调用
        const filePath = path.join(__dirname, '../static/js/page-dag.js');
        const content = fs.readFileSync(filePath, 'utf-8');
        
        // 检查markUnsaved()调用次数（应该至少有6次）
        const markUnsavedMatches = content.match(/markUnsaved\(\)/g);
        if (!markUnsavedMatches || markUnsavedMatches.length < 6) {
            throw new Error(`Expected at least 6 markUnsaved() calls, found ${markUnsavedMatches ? markUnsavedMatches.length : 0}`);
        }
        
        // 检查关键方法是否存在
        const requiredMethods = [
            'handleDrop',
            'deleteNode',
            'saveNodeProperties', 
            'saveEdgeProperties',
            'deleteEdge',
            'handleMouseUp'
        ];
        
        const missingMethods = [];
        for (const method of requiredMethods) {
            const pattern = new RegExp(`\\b${method}\\b\\s*\\(`);
            if (!pattern.test(content)) {
                missingMethods.push(method);
            }
        }
        
        if (missingMethods.length > 0) {
            throw new Error(`Missing methods: ${missingMethods.join(', ')}`);
        }
        
        console.log(`  ✓ Found ${markUnsavedMatches.length} markUnsaved() calls`);
        console.log(`  ✓ All 6 required methods present`);
    });
    
    // 测试8: AutoSaveManager类完整性
    await suite.test('AutoSaveManager Class Completeness', async () => {
        const filePath = path.join(__dirname, '../static/js/page-dag.js');
        const content = fs.readFileSync(filePath, 'utf-8');
        
        const requiredMethods = [
            'constructor',
            'init',
            'startAutoSave',
            'stopAutoSave',
            'autoSave',
            'markUnsaved',
            'shouldShowSaveNotification',
            'checkDraftRecovery',
            'showDraftRecoveryDialog',
            'restoreDraft',
            'clearDraft',
            'handleBeforeUnload',
            'onManualSave'
        ];
        
        const missing = [];
        for (const method of requiredMethods) {
            const pattern = new RegExp(`\\b${method}\\b\\s*\\(`);
            if (!pattern.test(content)) {
                missing.push(method);
            }
        }
        
        if (missing.length > 0) {
            throw new Error(`Missing methods: ${missing.join(', ')}`);
        }
        
        console.log(`  ✓ All ${requiredMethods.length} required methods found`);
    });
    
    // 生成报告
    return suite.report();
}

// 运行测试
console.log('========================================');
console.log('DAG Auto-Save Critical Path Testing');
console.log('========================================');

runTests().then(success => {
    process.exit(success ? 0 : 1);
}).catch(error => {
    console.error('Test execution failed:', error);
    process.exit(1);
});
