// API基础URL（自动检测）
const API_BASE_URL = window.location.origin;

// 全局变量
let trendChart = null;
let currentPeriod = 'D';
let currentTheme = 'light';

// DOM元素
const elements = {
    stockCode: document.getElementById('stockCode'),
    period: document.getElementById('period'),
    buyThreshold: document.getElementById('buyThreshold'),
    startDate: document.getElementById('startDate'),
    endDate: document.getElementById('endDate'),
    btnCalculate: document.getElementById('btnCalculate'),
    themeSwitcher: document.getElementById('themeSwitcher'),
    loading: document.getElementById('loading'),
    statisticsSection: document.getElementById('statisticsSection'),
    chartSection: document.getElementById('chartSection'),
    dataSection: document.getElementById('dataSection'),
    totalRecords: document.getElementById('totalRecords'),
    buySignals: document.getElementById('buySignals'),
    sellSignals: document.getElementById('sellSignals'),
    oversold: document.getElementById('oversold'),
    overbought: document.getElementById('overbought'),
    buySignalsBody: document.getElementById('buySignalsBody'),
    sellSignalsBody: document.getElementById('sellSignalsBody'),
    recentDataBody: document.getElementById('recentDataBody')
};

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    // 初始化主题
    initTheme();
    
    // 绑定事件
    elements.btnCalculate.addEventListener('click', handleCalculate);
    elements.period.addEventListener('change', (e) => {
        currentPeriod = e.target.value;
    });
    
    // 绑定主题切换事件
    if (elements.themeSwitcher) {
        elements.themeSwitcher.addEventListener('click', toggleTheme);
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
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
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

// 处理API响应错误
function handleApiError(response, data) {
    if (response.status === 401) {
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

    if (!stockCode) {
        alert('请输入股票代码');
        return;
    }

    if (startDate && endDate && startDate > endDate) {
        alert('开始日期不能晚于结束日期');
        return;
    }

    showLoading();

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
            credentials: 'same-origin'
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
    elements.totalRecords.textContent = data.total_records.toLocaleString();
    elements.buySignals.textContent = data.statistics.buy_signals_count;
    elements.sellSignals.textContent = data.statistics.sell_signals_count;
    elements.oversold.textContent = data.statistics.oversold_count;
    elements.overbought.textContent = data.statistics.overbought_count;

    elements.statisticsSection.style.display = 'block';
    displayBuySignals(data.buy_signals);
    displaySellSignals(data.sell_signals);
    displayRecentData(data.recent_data);
    displayChart(data.recent_data);
    elements.dataSection.style.display = 'block';
    elements.chartSection.style.display = 'block';
    switchTab('buySignals');
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
    const chartData = [...data].reverse();

    if (trendChart) {
        trendChart.destroy();
    }

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
    
    if (trendChart) {
        updateChartTheme();
    }
}

function updateChartTheme() {
    if (!trendChart) return;
    
    const isDark = currentTheme === 'dark';
    const gridColor = isDark ? 'rgba(148, 163, 184, 0.1)' : 'rgba(0, 0, 0, 0.1)';
    const textColor = isDark ? '#f1f5f9' : '#1e293b';
    
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
    
    trendChart.update('none');
}



