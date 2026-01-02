// API基础URL（自动检测）
const API_BASE_URL = window.location.origin;

// 全局变量
let trendChart = null;
let currentPeriod = 'D';
let currentTheme = 'light'; // 当前主题：'light' 或 'dark'

// DOM元素
const elements = {
    stockCode: document.getElementById('stockCode'),
    period: document.getElementById('period'),
    buyThreshold: document.getElementById('buyThreshold'),
    startDate: document.getElementById('startDate'),
    endDate: document.getElementById('endDate'),
    btnCalculate: document.getElementById('btnCalculate'),
    btnBacktest: document.getElementById('btnBacktest'),
    backtestPanel: document.getElementById('backtestPanel'),
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
    statisticsSection: document.getElementById('statisticsSection'),
    backtestSection: document.getElementById('backtestSection'),
    chartSection: document.getElementById('chartSection'),
    dataSection: document.getElementById('dataSection'),
    totalRecords: document.getElementById('totalRecords'),
    buySignals: document.getElementById('buySignals'),
    sellSignals: document.getElementById('sellSignals'),
    oversold: document.getElementById('oversold'),
    overbought: document.getElementById('overbought'),
    totalProfit: document.getElementById('totalProfit'),
    totalProfitRate: document.getElementById('totalProfitRate'),
    annualProfitRate: document.getElementById('annualProfitRate'),
    totalTrades: document.getElementById('totalTrades'),
    backtestPeriod: document.getElementById('backtestPeriod'),
    buySignalsBody: document.getElementById('buySignalsBody'),
    sellSignalsBody: document.getElementById('sellSignalsBody'),
    recentDataBody: document.getElementById('recentDataBody'),
    tradesBody: document.getElementById('tradesBody')
};

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    // 初始化主题
    initTheme();
    
    // 绑定事件
    elements.btnCalculate.addEventListener('click', handleCalculate);
    elements.btnBacktest.addEventListener('click', handleBacktest);
    elements.period.addEventListener('change', (e) => {
        currentPeriod = e.target.value;
    });
    
    // 绑定主题切换事件
    if (elements.themeSwitcher) {
        elements.themeSwitcher.addEventListener('click', toggleTheme);
    }
    
    // 绑定卖出策略选择事件
    if (elements.sellStrategies) {
        elements.sellStrategies.addEventListener('change', updateSellStrategyGroups);
        // 初始化显示/隐藏策略参数组
        updateSellStrategyGroups();
    }

    // 标签页切换
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const tabName = e.target.dataset.tab;
            switchTab(tabName);
        });
    });
});

// 切换标签页
function switchTab(tabName) {
    // 移除所有活动状态
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

    // 激活选中的标签
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(`${tabName}Tab`).classList.add('active');
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
    elements.statisticsSection.style.display = 'none';
    elements.backtestSection.style.display = 'none';
    elements.chartSection.style.display = 'none';
    elements.dataSection.style.display = 'none';
}

// 格式化数字（保留3位小数，与Excel表格一致）
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
        // 未授权，重定向到登录页面
        alert('登录已过期，请重新登录');
        window.location.href = '/login';
        return true;
    }
    return false;
}

// 处理计算指标
async function handleCalculate() {
    const period = elements.period.value;
    const stockCode = elements.stockCode.value.trim();
    const startDate = elements.startDate.value || null;
    const endDate = elements.endDate.value || null;
    
    currentPeriod = period;

    // 验证股票代码
    if (!stockCode) {
        alert('请输入股票代码');
        return;
    }

    // 验证日期范围
    if (startDate && endDate && startDate > endDate) {
        alert('开始日期不能晚于结束日期');
        return;
    }

    showLoading();

    // 获取买入阈值
    const buyThresholdValue = elements.buyThreshold.value.trim();
    const buyThreshold = buyThresholdValue ? parseFloat(buyThresholdValue) : null;

    try {
        const requestBody = {
            period,
            stock_code: stockCode
        };
        
        if (startDate) {
            requestBody.start_date = startDate;
        }
        if (endDate) {
            requestBody.end_date = endDate;
        }
        
        // 如果设置了买入阈值，添加到请求中
        if (buyThreshold !== null) {
            if (isNaN(buyThreshold) || buyThreshold < 0 || buyThreshold > 100) {
                alert('买入信号阈值必须在0-100之间');
                return;
            }
            requestBody.buy_threshold = buyThreshold;
        }

        const response = await fetch(`${API_BASE_URL}/api/calculate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody),
            credentials: 'same-origin'  // 包含cookie
        });

        const data = await response.json();

        if (handleApiError(response, data)) {
            return;
        }

        if (data.success) {
            displayCalculateResults(data);
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

// 显示计算结果
function displayCalculateResults(data) {
    // 显示统计信息
    elements.totalRecords.textContent = data.total_records.toLocaleString();
    elements.buySignals.textContent = data.statistics.buy_signals_count;
    elements.sellSignals.textContent = data.statistics.sell_signals_count;
    elements.oversold.textContent = data.statistics.oversold_count;
    elements.overbought.textContent = data.statistics.overbought_count;

    elements.statisticsSection.style.display = 'block';

    // 显示买卖信号表格（分别显示在独立的标签页中）
    displayBuySignals(data.buy_signals);
    displaySellSignals(data.sell_signals);

    // 显示最近数据
    displayRecentData(data.recent_data);

    // 显示图表
    displayChart(data.recent_data);

    elements.dataSection.style.display = 'block';
    elements.chartSection.style.display = 'block';

    // 默认显示买入信号标签页
    switchTab('buySignals');

    // 隐藏回测相关
    document.querySelector('[data-tab="trades"]').style.display = 'none';
}

// 显示买入信号
function displayBuySignals(signals) {
    elements.buySignalsBody.innerHTML = '';
    
    if (signals.length === 0) {
        elements.buySignalsBody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: var(--text-secondary);">暂无买入信号</td></tr>';
        return;
    }

    signals.forEach(signal => {
        const row = document.createElement('tr');
        const reason = signal.reason || '趋势线从下向上穿越10';
        const ma20 = signal.ma20 !== undefined && signal.ma20 !== null ? formatNumber(signal.ma20) : '-';
        row.innerHTML = `
            <td>${signal.date}</td>
            <td>${formatNumber(signal.close)}</td>
            <td>${formatNumber(signal.trend_line)}</td>
            <td>${ma20}</td>
            <td>${reason}</td>
        `;
        elements.buySignalsBody.appendChild(row);
    });
}

// 显示卖出信号
function displaySellSignals(signals) {
    elements.sellSignalsBody.innerHTML = '';
    
    if (signals.length === 0) {
        elements.sellSignalsBody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: var(--text-secondary);">暂无卖出信号</td></tr>';
        return;
    }

    signals.forEach(signal => {
        const row = document.createElement('tr');
        const reason = signal.reason || '-';
        const ma20 = signal.ma20 !== undefined && signal.ma20 !== null ? formatNumber(signal.ma20) : '-';
        row.innerHTML = `
            <td>${signal.date}</td>
            <td>${formatNumber(signal.close)}</td>
            <td>${formatNumber(signal.trend_line)}</td>
            <td>${ma20}</td>
            <td>${reason}</td>
        `;
        elements.sellSignalsBody.appendChild(row);
    });
}

// 显示最近数据
function displayRecentData(data) {
    elements.recentDataBody.innerHTML = '';

    data.forEach(item => {
        const row = document.createElement('tr');
        const ma20 = item.ma20 !== undefined && item.ma20 !== null ? formatNumber(item.ma20) : '-';
        row.innerHTML = `
            <td>${item.date}</td>
            <td>${formatNumber(item.close)}</td>
            <td>${formatNumber(item.支撑)}</td>
            <td>${formatNumber(item.阻力)}</td>
            <td>${formatNumber(item.中线)}</td>
            <td>${formatNumber(item.趋势线)}</td>
            <td>${ma20}</td>
            <td>${item.买 === 1 ? '✅' : ''}</td>
            <td>${item.卖 === 1 ? '✅' : ''}</td>
        `;
        elements.recentDataBody.appendChild(row);
    });
}

// 显示图表
function displayChart(data) {
    const ctx = document.getElementById('trendChart').getContext('2d');

    // 反转数据顺序（因为数据已经是倒序的，但图表需要正序显示）
    const chartData = [...data].reverse();

    if (trendChart) {
        trendChart.destroy();
    }

    // 根据当前主题设置颜色
    const isDark = currentTheme === 'dark';
    const gridColor = isDark ? 'rgba(148, 163, 184, 0.1)' : 'rgba(0, 0, 0, 0.1)';
    const textColor = isDark ? '#f1f5f9' : '#1e293b';

    trendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: chartData.map(item => item.date),
            datasets: [
                {
                    label: '收盘价',
                    data: chartData.map(item => item.close),
                    borderColor: isDark ? '#60a5fa' : '#2563eb',
                    backgroundColor: isDark ? 'rgba(96, 165, 250, 0.1)' : 'rgba(37, 99, 235, 0.1)',
                    tension: 0.4,
                    fill: true
                },
                {
                    label: '趋势线',
                    data: chartData.map(item => item.趋势线),
                    borderColor: isDark ? '#34d399' : '#10b981',
                    backgroundColor: isDark ? 'rgba(52, 211, 153, 0.1)' : 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4,
                    yAxisID: 'y1'
                },
                {
                    label: '支撑',
                    data: chartData.map(item => item.支撑),
                    borderColor: isDark ? '#f87171' : '#ef4444',
                    borderDash: [5, 5],
                    tension: 0.4
                },
                {
                    label: '阻力',
                    data: chartData.map(item => item.阻力),
                    borderColor: isDark ? '#fbbf24' : '#f59e0b',
                    borderDash: [5, 5],
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: textColor
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                x: {
                    ticks: {
                        color: textColor
                    },
                    grid: {
                        color: gridColor
                    }
                },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: '价格',
                        color: textColor
                    },
                    ticks: {
                        color: textColor
                    },
                    grid: {
                        color: gridColor
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: '趋势线',
                        color: textColor
                    },
                    ticks: {
                        color: textColor
                    },
                    grid: {
                        drawOnChartArea: false,
                        color: gridColor
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
}

// 更新卖出策略参数组的显示/隐藏
function updateSellStrategyGroups() {
    if (!elements.sellStrategies) return;
    
    const selectedStrategies = Array.from(elements.sellStrategies.selectedOptions).map(opt => opt.value);
    
    // 显示/隐藏对应的参数组
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
        ['stop_loss', 'take_profit', 'below_ma20']; // 默认全选
    
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

    // 验证股票代码
    if (!stockCode) {
        alert('请输入股票代码');
        return;
    }

    if (!initialAmount || initialAmount <= 0) {
        alert('请输入有效的初始资金金额');
        return;
    }

    // 验证日期范围
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
        
        // 根据选中的策略添加参数
        if (selectedStrategies.includes('stop_loss') && stopLossPercent !== null) {
            requestBody.stop_loss_percent = stopLossPercent;
        }
        
        if (selectedStrategies.includes('take_profit') && takeProfitPercent !== null) {
            requestBody.take_profit_percent = takeProfitPercent;
        }
        
        if (selectedStrategies.includes('below_ma20') && belowMa20Days !== null) {
            requestBody.below_ma20_days = belowMa20Days;
        }
        
        // 如果设置了买入阈值，添加到请求中
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
            credentials: 'same-origin'  // 包含cookie
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
        // 如果没有配置，使用默认值（红涨绿跌）
        return value >= 0 ? '#ef4444' : '#10b981';
    }
    return value >= 0 ? window.STOCK_COLORS.rise : window.STOCK_COLORS.fall;
}

// 显示回测结果
function displayBacktestResults(data) {
    // 显示回测统计
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

    // 显示交易记录
    displayTrades(data.trades);

    // 切换到交易记录标签
    document.querySelector('[data-tab="trades"]').style.display = 'block';
    switchTab('trades');

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

// 显示回测面板
elements.btnBacktest.addEventListener('click', () => {
    elements.backtestPanel.style.display = 'block';
});

// 主题管理函数
function initTheme() {
    // 从localStorage读取保存的主题
    const savedTheme = localStorage.getItem('stockAppTheme') || 'light';
    setTheme(savedTheme);
}

function toggleTheme() {
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    // 保存到localStorage
    localStorage.setItem('stockAppTheme', newTheme);
}

function setTheme(theme) {
    currentTheme = theme;
    const html = document.documentElement;
    
    if (theme === 'dark') {
        html.setAttribute('data-theme', 'dark');
        // 更新主题切换器图标和文本
        if (elements.themeSwitcher) {
            elements.themeSwitcher.innerHTML = `
                <span class="theme-switcher-icon">☀️</span>
                <span class="theme-switcher-text">浅色</span>
            `;
        }
    } else {
        html.setAttribute('data-theme', 'light');
        // 更新主题切换器图标和文本
        if (elements.themeSwitcher) {
            elements.themeSwitcher.innerHTML = `
                <span class="theme-switcher-icon">🌙</span>
                <span class="theme-switcher-text">深色</span>
            `;
        }
    }
    
    // 如果图表存在，需要更新图表主题
    if (trendChart) {
        updateChartTheme();
    }
}

function updateChartTheme() {
    if (!trendChart) return;
    
    const isDark = currentTheme === 'dark';
    const gridColor = isDark ? 'rgba(148, 163, 184, 0.1)' : 'rgba(0, 0, 0, 0.1)';
    const textColor = isDark ? '#f1f5f9' : '#1e293b';
    
    // 更新图表配置
    if (trendChart.options.scales) {
        if (trendChart.options.scales.x) {
            trendChart.options.scales.x.ticks.color = textColor;
            trendChart.options.scales.x.grid.color = gridColor;
        }
        if (trendChart.options.scales.y) {
            trendChart.options.scales.y.ticks.color = textColor;
            trendChart.options.scales.y.grid.color = gridColor;
        }
        if (trendChart.options.scales.y1) {
            trendChart.options.scales.y1.ticks.color = textColor;
            trendChart.options.scales.y1.grid.color = gridColor;
        }
    }
    
    if (trendChart.options.plugins && trendChart.options.plugins.legend) {
        trendChart.options.plugins.legend.labels.color = textColor;
    }
    
    trendChart.update('none'); // 使用'none'模式避免动画闪烁
}

