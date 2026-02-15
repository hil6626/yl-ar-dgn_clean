/**
 * Dashboard卡片点击反馈组件
 * 版本: v1.0.0
 */

export class CardFeedback {
  constructor() {
    this.activeCards = new Set();
  }

  /**
   * 添加点击反馈
   * @param {HTMLElement} card - 卡片元素
   */
  addClickFeedback(card) {
    if (!card || this.activeCards.has(card)) return;

    this.activeCards.add(card);

    card.addEventListener('click', (e) => {
      // 添加点击动画类
      card.classList.add('card-clicked');

      // 创建涟漪效果
      this.createRipple(card, e);

      // 显示加载状态
      this.showLoadingState(card);

      // 300ms后移除动画类
      setTimeout(() => {
        card.classList.remove('card-clicked');
        this.hideLoadingState(card);
      }, 300);
    });
  }

  /**
   * 创建涟漪效果
   * @param {HTMLElement} card - 卡片元素
   * @param {Event} e - 点击事件
   */
  createRipple(card, e) {
    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const ripple = document.createElement('span');
    ripple.className = 'card-ripple';
    ripple.style.cssText = `
      position: absolute;
      left: ${x}px;
      top: ${y}px;
      width: 20px;
      height: 20px;
      background: rgba(255, 255, 255, 0.3);
      border-radius: 50%;
      transform: translate(-50%, -50%) scale(0);
      animation: ripple-effect 0.6s ease-out;
      pointer-events: none;
    `;

    card.style.position = 'relative';
    card.style.overflow = 'hidden';
    card.appendChild(ripple);

    // 添加动画样式
    if (!document.getElementById('ripple-style')) {
      const style = document.createElement('style');
      style.id = 'ripple-style';
      style.textContent = `
        @keyframes ripple-effect {
          to {
            transform: translate(-50%, -50%) scale(20);
            opacity: 0;
          }
        }
        .card-clicked {
          transform: scale(0.98);
          transition: transform 0.15s ease;
        }
      `;
      document.head.appendChild(style);
    }

    // 移除涟漪元素
    setTimeout(() => ripple.remove(), 600);
  }

  /**
   * 显示加载状态
   * @param {HTMLElement} card - 卡片元素
   */
  showLoadingState(card) {
    const icon = card.querySelector('.stat-icon');
    if (icon) {
      icon.classList.add('loading-pulse');
    }
  }

  /**
   * 隐藏加载状态
   * @param {HTMLElement} card - 卡片元素
   */
  hideLoadingState(card) {
    const icon = card.querySelector('.stat-icon');
    if (icon) {
      icon.classList.remove('loading-pulse');
    }
  }

  /**
   * 初始化所有卡片
   */
  initAllCards() {
    document.querySelectorAll('.stat-card').forEach(card => {
      this.addClickFeedback(card);
    });
  }
}
