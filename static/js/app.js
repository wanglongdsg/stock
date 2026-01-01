// API基础URL（自动检测）
const API_BASE_URL = window.location.origin;

// 全局变量
let trendChart = null;
let currentPeriod = 'D';

// DOM元素
const elements = {
    stockCode: document.getElementById('stockCode'),
    period: document.getElementById('period'),
    startDate: document.getElementById('startDate'),
    endDate: document.getElementById('endDate'),
    btnCalculate: document.getElementById('btnCalculate'),
    btnBacktest: document.getElementById('btnBacktest'),
    backtestPanel: document.getElementById('backtestPanel'),
    initialAmount: document.getElementById('initialAmount'),
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
    // 绑定事件
    elements.btnCalculate.addEventListener('click', handleCalculate);
    elements.btnBacktest.addEventListener('click', handleBacktest);
    elements.period.addEventListener('change', (e) => {
        currentPeriod = e.target.value;
    });

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

// 格式化数字
function formatNumber(num) {
    if (num === null || num === undefined) return '-';
    return new Intl.NumberFormat('zh-CN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
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

    // 显示买卖信号表格
    displayBuySignals(data.buy_signals);
    displaySellSignals(data.sell_signals);

    // 显示最近数据
    displayRecentData(data.recent_data);

    // 显示图表
    displayChart(data.recent_data);

    elements.dataSection.style.display = 'block';
    elements.chartSection.style.display = 'block';

    // 隐藏回测相关
    document.querySelector('[data-tab="trades"]').style.display = 'none';
}

// 显示买入信号
function displayBuySignals(signals) {
    elements.buySignalsBody.innerHTML = '';
    
    if (signals.length === 0) {
        elements.buySignalsBody.innerHTML = '<tr><td colspan="3" style="text-align: center; color: var(--text-secondary);">暂无买入信号</td></tr>';
        return;
    }

    signals.forEach(signal => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${signal.date}</td>
            <td>${formatNumber(signal.close)}</td>
            <td>${formatNumber(signal.trend_line)}</td>
        `;
        elements.buySignalsBody.appendChild(row);
    });
}

// 显示卖出信号
function displaySellSignals(signals) {
    elements.sellSignalsBody.innerHTML = '';
    
    if (signals.length === 0) {
        elements.sellSignalsBody.innerHTML = '<tr><td colspan="3" style="text-align: center; color: var(--text-secondary);">暂无卖出信号</td></tr>';
        return;
    }

    signals.forEach(signal => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${signal.date}</td>
            <td>${formatNumber(signal.close)}</td>
            <td>${formatNumber(signal.trend_line)}</td>
        `;
        elements.sellSignalsBody.appendChild(row);
    });
}

// 显示最近数据
function displayRecentData(data) {
    elements.recentDataBody.innerHTML = '';

    data.forEach(item => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${item.date}</td>
            <td>${formatNumber(item.close)}</td>
            <td>${formatNumber(item.支撑)}</td>
            <td>${formatNumber(item.阻力)}</td>
            <td>${formatNumber(item.中线)}</td>
            <td>${formatNumber(item.趋势线)}</td>
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

    trendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: chartData.map(item => item.date),
            datasets: [
                {
                    label: '收盘价',
                    data: chartData.map(item => item.close),
                    borderColor: '#2563eb',
                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                    tension: 0.4,
                    fill: true
                },
                {
                    label: '趋势线',
                    data: chartData.map(item => item.趋势线),
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4,
                    yAxisID: 'y1'
                },
                {
                    label: '支撑',
                    data: chartData.map(item => item.支撑),
                    borderColor: '#ef4444',
                    borderDash: [5, 5],
                    tension: 0.4
                },
                {
                    label: '阻力',
                    data: chartData.map(item => item.阻力),
                    borderColor: '#f59e0b',
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
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: '价格'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: '趋势线'
                    },
                    grid: {
                        drawOnChartArea: false
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

// 处理回测
async function handleBacktest() {
    const period = elements.period.value;
    const stockCode = elements.stockCode.value.trim();
    const startDate = elements.startDate.value || null;
    const endDate = elements.endDate.value || null;
    const initialAmount = parseFloat(elements.initialAmount.value);

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
            initial_amount: initialAmount
        };
        
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
        elements.tradesBody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--text-secondary);">暂无交易记录</td></tr>';
        return;
    }

    trades.forEach(trade => {
        const row = document.createElement('tr');
        const profitColor = getPriceColor(trade.profit);
        const profitStyle = `color: ${profitColor}`;
        row.innerHTML = `
            <td>${trade.buy_date}</td>
            <td>${formatNumber(trade.buy_price)}</td>
            <td>${trade.sell_date}</td>
            <td>${formatNumber(trade.sell_price)}</td>
            <td>${formatNumber(trade.shares)}</td>
            <td style="${profitStyle}">${formatNumber(trade.profit)}</td>
            <td style="${profitStyle}">${formatPercent(trade.profit_rate)}</td>
        `;
        elements.tradesBody.appendChild(row);
    });
}

// 显示回测面板
elements.btnBacktest.addEventListener('click', () => {
    elements.backtestPanel.style.display = 'block';
});

