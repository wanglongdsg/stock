// API基础URL（自动检测）
const API_BASE_URL = window.location.origin;

// 全局变量
let currentTheme = 'light';

// DOM元素
const elements = {
    stockCode: document.getElementById('stockCode'),
    period: document.getElementById('period'),
    buyThreshold: document.getElementById('buyThreshold'),
    startDate: document.getElementById('startDate'),
    endDate: document.getElementById('endDate'),
    btnBacktest: document.getElementById('btnBacktest'),
    initialAmount: document.getElementById('initialAmount'),
    sellStrategies: document.getElementById('sellStrategies'),
    stopLossPercent: document.getElementById('stopLossPercent'),
    takeProfitPercent: document.getElementById('takeProfitPercent'),
    belowMa20Days: document.getElementById('belowMa20Days'),
    stopLossGroup: document.getElementById('stopLossGroup'),
    takeProfitGroup: document.getElementById('takeProfitGroup'),
    belowMa20Group: document.getElementById('belowMa20Group'),
    themeSwitcher: document.getElementById('themeSwitcher'),
    loading: document.getElementById('loading'),
    backtestSection: document.getElementById('backtestSection'),
    dataSection: document.getElementById('dataSection'),
    totalProfit: document.getElementById('totalProfit'),
    totalProfitRate: document.getElementById('totalProfitRate'),
    annualProfitRate: document.getElementById('annualProfitRate'),
    totalTrades: document.getElementById('totalTrades'),
    backtestPeriod: document.getElementById('backtestPeriod'),
    tradesBody: document.getElementById('tradesBody')
};

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    // 初始化主题
    initTheme();
    
    // 绑定事件
    elements.btnBacktest.addEventListener('click', handleBacktest);
    
    // 绑定主题切换事件
    if (elements.themeSwitcher) {
        elements.themeSwitcher.addEventListener('click', toggleTheme);
    }
    
    // 绑定卖出策略选择事件
    if (elements.sellStrategies) {
        elements.sellStrategies.addEventListener('change', updateSellStrategyGroups);
        updateSellStrategyGroups();
    }
});

// 更新卖出策略参数组的显示/隐藏
function updateSellStrategyGroups() {
    if (!elements.sellStrategies) return;
    
    const selectedStrategies = Array.from(elements.sellStrategies.selectedOptions).map(opt => opt.value);
    
    if (elements.stopLossGroup) {
        elements.stopLossGroup.classList.toggle('hidden', !selectedStrategies.includes('stop_loss'));
    }
    if (elements.takeProfitGroup) {
        elements.takeProfitGroup.classList.toggle('hidden', !selectedStrategies.includes('take_profit'));
    }
    if (elements.belowMa20Group) {
        elements.belowMa20Group.classList.toggle('hidden', !selectedStrategies.includes('below_ma20'));
    }
}

// 显示加载状态
function showLoading() {
    elements.loading.style.display = 'block';
    hideAllSections();
}

// 隐藏加载状态
function hideLoading() {
    elements.loading.style.display = 'none';
}

// 隐藏所有区域
function hideAllSections() {
    elements.backtestSection.style.display = 'none';
    elements.dataSection.style.display = 'none';
}

// 格式化数字（保留3位小数）
function formatNumber(num) {
    if (num === null || num === undefined) return '-';
    return new Intl.NumberFormat('zh-CN', {
        minimumFractionDigits: 3,
        maximumFractionDigits: 3
    }).format(num);
}

// 格式化百分比
function formatPercent(num) {
    if (num === null || num === undefined) return '-';
    return `${num >= 0 ? '+' : ''}${num.toFixed(2)}%`;
}

// 处理API响应错误
function handleApiError(response, data) {
    if (response.status === 401) {
        alert('登录已过期，请重新登录');
        window.location.href = '/login';
        return true;
    }
    return false;
}

// 处理回测
async function handleBacktest() {
    const period = elements.period.value;
    const stockCode = elements.stockCode.value.trim();
    const startDate = elements.startDate.value || null;
    const endDate = elements.endDate.value || null;
    const initialAmount = parseFloat(elements.initialAmount.value);
    
    // 获取选中的卖出策略
    const selectedStrategies = elements.sellStrategies ? 
        Array.from(elements.sellStrategies.selectedOptions).map(opt => opt.value) : 
        ['stop_loss', 'take_profit', 'below_ma20'];
    
    if (selectedStrategies.length === 0) {
        alert('请至少选择一种卖出策略');
        return;
    }
    
    // 根据选中的策略获取参数
    let stopLossPercent = null;
    let takeProfitPercent = null;
    let belowMa20Days = null;
    
    if (selectedStrategies.includes('stop_loss')) {
        stopLossPercent = parseFloat(elements.stopLossPercent.value);
        if (isNaN(stopLossPercent) || stopLossPercent < 0 || stopLossPercent > 50) {
            alert('止损比例必须在0-50之间');
            return;
        }
    }
    
    if (selectedStrategies.includes('take_profit')) {
        const takeProfitPercentValue = elements.takeProfitPercent.value.trim();
        if (takeProfitPercentValue) {
            takeProfitPercent = parseFloat(takeProfitPercentValue);
            if (isNaN(takeProfitPercent) || takeProfitPercent < 0 || takeProfitPercent > 200) {
                alert('止盈比例必须在0-200之间');
                return;
            }
        }
    }
    
    if (selectedStrategies.includes('below_ma20')) {
        const belowMa20DaysValue = elements.belowMa20Days.value.trim();
        belowMa20Days = belowMa20DaysValue ? parseInt(belowMa20DaysValue) : 3;
        if (isNaN(belowMa20Days) || belowMa20Days < 1 || belowMa20Days > 30) {
            alert('20均线下方天数必须在1-30之间');
            return;
        }
    }
    
    const buyThresholdValue = elements.buyThreshold.value.trim();
    const buyThreshold = buyThresholdValue ? parseFloat(buyThresholdValue) : null;

    if (!stockCode) {
        alert('请输入股票代码');
        return;
    }

    if (!initialAmount || initialAmount <= 0) {
        alert('请输入有效的初始资金金额');
        return;
    }

    if (startDate && endDate && startDate > endDate) {
        alert('开始日期不能晚于结束日期');
        return;
    }

    showLoading();

    try {
        const requestBody = {
            period,
            stock_code: stockCode,
            initial_amount: initialAmount,
            sell_strategies: selectedStrategies
        };
        
        if (selectedStrategies.includes('stop_loss') && stopLossPercent !== null) {
            requestBody.stop_loss_percent = stopLossPercent;
        }
        
        if (selectedStrategies.includes('take_profit') && takeProfitPercent !== null) {
            requestBody.take_profit_percent = takeProfitPercent;
        }
        
        if (selectedStrategies.includes('below_ma20') && belowMa20Days !== null) {
            requestBody.below_ma20_days = belowMa20Days;
        }
        
        if (buyThreshold !== null) {
            if (isNaN(buyThreshold) || buyThreshold < 0 || buyThreshold > 100) {
                alert('买入信号阈值必须在0-100之间');
                return;
            }
            requestBody.buy_threshold = buyThreshold;
        }
        
        if (startDate) {
            requestBody.start_date = startDate;
        }
        if (endDate) {
            requestBody.end_date = endDate;
        }

        const response = await fetch(`${API_BASE_URL}/api/backtest`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody),
            credentials: 'same-origin'
        });

        const data = await response.json();

        if (handleApiError(response, data)) {
            return;
        }

        if (data.success) {
            displayBacktestResults(data);
        } else {
            alert(`错误: ${data.error}`);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('请求失败，请确保服务已启动');
    } finally {
        hideLoading();
    }
}

// 获取涨跌颜色
function getPriceColor(value) {
    if (!window.STOCK_COLORS) {
        return value >= 0 ? '#ef4444' : '#10b981';
    }
    return value >= 0 ? window.STOCK_COLORS.rise : window.STOCK_COLORS.fall;
}

// 显示回测结果
function displayBacktestResults(data) {
    const profitColor = getPriceColor(data.total_profit);
    const profitRateColor = getPriceColor(data.total_profit_rate);
    const annualRateColor = getPriceColor(data.annual_profit_rate);
    
    elements.totalProfit.textContent = formatNumber(data.total_profit);
    elements.totalProfit.style.color = profitColor;
    
    elements.totalProfitRate.textContent = formatPercent(data.total_profit_rate);
    elements.totalProfitRate.style.color = profitRateColor;
    
    elements.annualProfitRate.textContent = formatPercent(data.annual_profit_rate);
    elements.annualProfitRate.style.color = annualRateColor;
    
    elements.totalTrades.textContent = data.total_trades;
    elements.backtestPeriod.textContent = `${data.start_date} 至 ${data.end_date}`;

    elements.backtestSection.style.display = 'block';
    displayTrades(data.trades);
    elements.dataSection.style.display = 'block';
}

// 显示交易记录
function displayTrades(trades) {
    elements.tradesBody.innerHTML = '';

    if (trades.length === 0) {
        elements.tradesBody.innerHTML = '<tr><td colspan="8" style="text-align: center; color: var(--text-secondary);">暂无交易记录</td></tr>';
        return;
    }

    trades.forEach(trade => {
        const row = document.createElement('tr');
        const profitColor = getPriceColor(trade.profit);
        const profitStyle = `color: ${profitColor}`;
        const sellReason = trade.reason || '-';
        row.innerHTML = `
            <td>${trade.buy_date}</td>
            <td>${formatNumber(trade.buy_price)}</td>
            <td>${trade.sell_date}</td>
            <td>${formatNumber(trade.sell_price)}</td>
            <td>${formatNumber(trade.shares)}</td>
            <td style="${profitStyle}">${formatNumber(trade.profit)}</td>
            <td style="${profitStyle}">${formatPercent(trade.profit_rate)}</td>
            <td>${sellReason}</td>
        `;
        elements.tradesBody.appendChild(row);
    });
}

// 主题管理函数
function initTheme() {
    const savedTheme = localStorage.getItem('stockAppTheme') || 'light';
    setTheme(savedTheme);
}

function toggleTheme() {
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    localStorage.setItem('stockAppTheme', newTheme);
}

function setTheme(theme) {
    currentTheme = theme;
    const html = document.documentElement;
    
    if (theme === 'dark') {
        html.setAttribute('data-theme', 'dark');
        if (elements.themeSwitcher) {
            elements.themeSwitcher.innerHTML = `
                <span class="theme-switcher-icon">☀️</span>
                <span class="theme-switcher-text">浅色</span>
            `;
        }
    } else {
        html.setAttribute('data-theme', 'light');
        if (elements.themeSwitcher) {
            elements.themeSwitcher.innerHTML = `
                <span class="theme-switcher-icon">🌙</span>
                <span class="theme-switcher-text">深色</span>
            `;
        }
    }
}


