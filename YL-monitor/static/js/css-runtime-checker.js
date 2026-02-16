/**
 * CSS运行时检测工具
 * 在开发模式下检测动态添加的不存在CSS类
 * 版本: 1.0.0
 */

(function() {
    'use strict';
    
    // 只在开发模式启用
    const isDevMode = window.location.hostname === '0.0.0.0' || 
                      window.location.hostname === '127.0.0.1' ||
                      localStorage.getItem('css-dev-mode') === 'true';
    
    if (!isDevMode) return;
    
    console.log('🔧 CSS运行时检测工具已启用');
    
    // 已知的CSS类名缓存
    let knownClasses = new Set();
    let checkedElements = new WeakSet();
    let warningCount = 0;
    const MAX_WARNINGS = 50; // 防止过多警告
    
    /**
     * 收集所有已定义的CSS类名
     */
    function collectCSSClasses() {
        const classes = new Set();
        
        // 从所有样式表收集
        try {
            for (const sheet of document.styleSheets) {
                try {
                    for (const rule of sheet.cssRules || sheet.rules || []) {
                        if (rule.selectorText) {
                            // 提取类名
                            const classMatches = rule.selectorText.match(/\.([a-zA-Z][a-zA-Z0-9_-]*)/g);
                            if (classMatches) {
                                classMatches.forEach(match => {
                                    classes.add(match.substring(1)); // 去掉点号
                                });
                            }
                        }
                    }
                } catch (e) {
                    // 跨域样式表会抛出错误，忽略
                }
            }
        } catch (e) {
            console.warn('无法读取样式表:', e);
        }
        
        // 从所有元素收集已使用的类
        document.querySelectorAll('*').forEach(el => {
            if (el.className && typeof el.className === 'string') {
                el.className.split(/\s+/).forEach(cls => {
                    if (cls) classes.add(cls);
                });
            }
        });
        
        return classes;
    }
    
    /**
     * 检查元素类名是否存在对应CSS
     */
    function checkElementClasses(element) {
        if (checkedElements.has(element)) return;
        if (warningCount >= MAX_WARNINGS) return;
        
        checkedElements.add(element);
        
        if (!element.className || typeof element.className !== 'string') return;
        
        const classes = element.className.split(/\s+/).filter(Boolean);
        
        classes.forEach(className => {
            // 跳过动态类名模式（以-结尾的部分）
            if (className.includes('-')) {
                const baseName = className.split('-')[0];
                // 检查基础类名是否存在
                const possibleBases = [
                    baseName,
                    className.replace(/-[a-z]+$/, '') // 移除状态后缀
                ];
                
                const hasBase = possibleBases.some(base => 
                    knownClasses.has(base) || 
                    knownClasses.has(base + '-primary') ||
                    knownClasses.has(base + '-container')
                );
                
                if (hasBase) return; // 基础类名存在，可能是动态生成的
            }
            
            // 检查类名是否已知
            if (!knownClasses.has(className)) {
                // 可能是内联样式或动态生成的，延迟检查
                setTimeout(() => {
                    // 再次检查，可能CSS已加载
                    const updatedClasses = collectCSSClasses();
                    if (!updatedClasses.has(className) && warningCount < MAX_WARNINGS) {
                        warningCount++;
                        console.warn(
                            `⚠️ CSS类名未找到: ".${className}"`,
                            '\n元素:', element,
                            '\n建议: 检查CSS文件是否包含此类名，或添加到白名单'
                        );
                        
                        // 在元素上添加标记以便调试
                        element.setAttribute('data-css-warning', className);
                    }
                }, 1000);
            }
        });
    }
    
    /**
     * 初始化检测
     */
    function init() {
        // 收集初始类名
        knownClasses = collectCSSClasses();
        console.log(`📊 已收集 ${knownClasses.size} 个CSS类名`);
        
        // 检查现有元素
        document.querySelectorAll('*').forEach(checkElementClasses);
        
        // 监听DOM变化
        const observer = new MutationObserver((mutations) => {
            mutations.forEach(mutation => {
                mutation.addedNodes.forEach(node => {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        checkElementClasses(node);
                        // 检查子元素
                        node.querySelectorAll('*').forEach(checkElementClasses);
                    }
                });
                
                // 检查属性变化
                if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                    checkElementClasses(mutation.target);
                }
            });
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['class']
        });
        
        console.log('👁️ DOM观察器已启动');
    }
    
    /**
     * 手动触发检查
     */
    function recheck() {
        knownClasses = collectCSSClasses();
        warningCount = 0;
        checkedElements = new WeakSet();
        document.querySelectorAll('*').forEach(checkElementClasses);
        console.log('🔄 手动检查完成');
    }
    
    /**
     * 添加类名到白名单
     */
    function whitelist(className) {
        knownClasses.add(className);
        console.log(`✅ 已添加白名单: .${className}`);
    }
    
    /**
     * 显示统计信息
     */
    function stats() {
        console.log('📈 CSS统计信息:');
        console.log(`   已知类名: ${knownClasses.size}`);
        console.log(`   警告次数: ${warningCount}`);
        console.log(`   开发模式: ${isDevMode ? '是' : '否'}`);
    }
    
    // 暴露API到全局
    window.CSSChecker = {
        recheck: recheck,
        whitelist: whitelist,
        stats: stats,
        isDevMode: isDevMode
    };
    
    // 页面加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // 定期重新收集类名（处理懒加载CSS）
    setInterval(() => {
        const newClasses = collectCSSClasses();
        if (newClasses.size > knownClasses.size) {
            const added = newClasses.size - knownClasses.size;
            knownClasses = newClasses;
            console.log(`📥 新增 ${added} 个CSS类名（总计: ${knownClasses.size}）`);
        }
    }, 5000);
})();
