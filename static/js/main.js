/**
 * 靠山Pizza管理系统主JavaScript文件
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('靠山Pizza管理系统初始化完成');

    // 初始化侧边栏导航高亮
    initNavHighlight();

    // 初始化工具提示
    initTooltips();

    // 初始化通知功能
    initNotifications();

    // Check if we're on the dashboard page
    if (window.location.pathname === '/' || window.location.pathname.includes('/dashboard')) {
        // Poll for order status updates from other tabs
        let lastUpdateCheck = Date.now();
        setInterval(function() {
            const orderStatusUpdated = localStorage.getItem('orderStatusUpdated');
            if (orderStatusUpdated && parseInt(orderStatusUpdated) > lastUpdateCheck) {
                console.log('Order status updated in another tab, refreshing dashboard data');
                lastUpdateCheck = Date.now();

                // Refresh dashboard charts if functions exist
                if (typeof loadSalesData === 'function') {
                    loadSalesData();
                }
                if (typeof loadSalesTrend === 'function') {
                    loadSalesTrend();
                }
                if (typeof loadRevenueByChannel === 'function') {
                    loadRevenueByChannel();
                }
                if (typeof loadTopSellingItems === 'function') {
                    loadTopSellingItems();
                }
            }
        }, 5000); // Check every 5 seconds
    }
});

/**
 * 初始化侧边栏导航高亮
 */
function initNavHighlight() {
    // 获取当前路径
    const currentPath = window.location.pathname;

    // 查找所有导航链接
    const navLinks = document.querySelectorAll('#menu a.nav-link');

    // 移除所有active类
    navLinks.forEach(link => link.classList.remove('active'));

    // 查找匹配当前路径的链接并添加active类
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (currentPath === href || (href !== '/' && currentPath.startsWith(href))) {
            link.classList.add('active');
        }
    });
}

/**
 * 初始化Bootstrap工具提示
 */
function initTooltips() {
    // 检查是否存在Bootstrap的工具提示功能
    if (typeof bootstrap !== 'undefined' && typeof bootstrap.Tooltip !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}

/**
 * 初始化通知功能
 */
function initNotifications() {
    // 通知计数器
    const notificationCount = document.querySelector('.notification-count');
    if (notificationCount) {
        updateNotificationCount();
    }

    // 绑定通知点击事件
    const notificationItems = document.querySelectorAll('.notification-item');
    notificationItems.forEach(item => {
        item.addEventListener('click', function() {
            markNotificationRead(this.dataset.id);
        });
    });
}

/**
 * 更新通知计数
 */
function updateNotificationCount() {
    // 这里应该是一个AJAX请求来获取未读通知数量
    // 示例代码仅用于演示
    fetch('/api/notifications/unread-count')
        .then(response => response.json())
        .then(data => {
            const notificationCount = document.querySelector('.notification-count');
            if (notificationCount) {
                notificationCount.textContent = data.count;
                notificationCount.style.display = data.count > 0 ? 'inline-block' : 'none';
            }
        })
        .catch(error => console.error('获取通知计数时出错:', error));
}

/**
 * 标记通知为已读
 * @param {string} id 通知ID
 */
function markNotificationRead(id) {
    // 这里应该是一个AJAX请求来标记通知为已读
    // 示例代码仅用于演示
    fetch(`/api/notifications/${id}/mark-read`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // 更新UI
                const notificationItem = document.querySelector(`.notification-item[data-id="${id}"]`);
                if (notificationItem) {
                    notificationItem.classList.remove('unread');
                }
                updateNotificationCount();
            }
        })
        .catch(error => console.error('标记通知为已读时出错:', error));
}

/**
 * 格式化日期时间
 * @param {string|Date} dateTime 日期时间字符串或Date对象
 * @param {string} format 格式化模式 (short, medium, long)
 * @returns {string} 格式化后的日期时间字符串
 */
function formatDateTime(dateTime, format = 'medium') {
    const date = typeof dateTime === 'string' ? new Date(dateTime) : dateTime;

    if (isNaN(date.getTime())) {
        return dateTime; // 如果日期无效，返回原始值
    }

    const options = {
        short: { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' },
        medium: { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' },
        long: { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' }
    };

    return date.toLocaleDateString('zh-CN', options[format] || options.medium);
}

/**
 * 格式化货币
 * @param {number} amount 金额
 * @param {string} currency 货币单位，默认为CNY
 * @returns {string} 格式化后的货币字符串
 */
function formatCurrency(amount, currency = 'CNY') {
    return new Intl.NumberFormat('zh-CN', {
        style: 'currency',
        currency: currency
    }).format(amount);
}

/**
 * 显示提示消息
 * @param {string} message 消息内容
 * @param {string} type 消息类型 (success, info, warning, error)
 * @param {number} duration 显示时长，单位毫秒
 */
function showToast(message, type = 'info', duration = 3000) {
    // 创建toast元素
    const toast = document.createElement('div');
    toast.className = `toast-notification toast-${type}`;
    toast.innerHTML = `
        <div class="toast-icon">
            <i class="bi ${getToastIcon(type)}"></i>
        </div>
        <div class="toast-message">${message}</div>
        <button class="toast-close">&times;</button>
    `;

    // 添加到页面
    document.body.appendChild(toast);

    // 显示动画
    setTimeout(() => {
        toast.classList.add('show');
    }, 10);

    // 绑定关闭按钮事件
    const closeButton = toast.querySelector('.toast-close');
    closeButton.addEventListener('click', () => {
        closeToast(toast);
    });

    // 自动关闭
    if (duration > 0) {
        setTimeout(() => {
            closeToast(toast);
        }, duration);
    }
}

/**
 * 关闭提示消息
 * @param {HTMLElement} toast 提示消息元素
 */
function closeToast(toast) {
    toast.classList.remove('show');
    toast.classList.add('hide');

    // 动画结束后移除元素
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 300);
}

/**
 * 获取提示消息图标
 * @param {string} type 消息类型
 * @returns {string} 图标类名
 */
function getToastIcon(type) {
    switch (type) {
        case 'success':
            return 'bi-check-circle-fill';
        case 'warning':
            return 'bi-exclamation-triangle-fill';
        case 'error':
            return 'bi-x-circle-fill';
        case 'info':
        default:
            return 'bi-info-circle-fill';
    }
}

/**
 * 发送API请求
 * @param {string} url 请求地址
 * @param {Object} options 请求选项
 * @returns {Promise} 请求结果Promise
 */
async function apiRequest(url, options = {}) {
    const defaultOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    };

    const requestOptions = {...defaultOptions, ...options };

    try {
        const response = await fetch(url, requestOptions);

        // 检查响应状态
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        // 解析JSON响应
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('API请求错误:', error);
        showToast('请求失败，请稍后重试', 'error');
        throw error;
    }
}

// Global function to update all charts on a page
function refreshAllCharts() {
    // Find all chart objects on the page
    if (window.charts) {
        Object.keys(window.charts).forEach(chartId => {
            if (window.charts[chartId]) {
                console.log(`Refreshing chart: ${chartId}`);
                if (typeof window.chartLoaders[chartId] === 'function') {
                    window.chartLoaders[chartId]();
                }
            }
        });
    }
}