// assets/charts.js
(function () {
  var style = getComputedStyle(document.documentElement);
  var accent = style.getPropertyValue('--accent').trim();
  var accent2 = style.getPropertyValue('--accent2').trim();
  var ink = style.getPropertyValue('--ink').trim();
  var muted = style.getPropertyValue('--muted').trim();
  var rule = style.getPropertyValue('--rule').trim();
  var bg2 = style.getPropertyValue('--bg2').trim();

  var el = document.getElementById('chart-effort');
  if (!el) return;

  var chart = echarts.init(el, null, { renderer: 'svg' });

  var labels = [
    '知识库与 RAG 问答',
    '数据底座（库 / 存储 / 录入）',
    'AI 咨询与对话',
    '任务梳理',
    '综合看板整合',
    '报告 / 文档 / PPT 生成',
    '工作流审查与数据分析'
  ].reverse();

  var values = [25, 20, 15, 15, 15, 10, 10].reverse();

  chart.setOption({
    animation: false,
    grid: { left: 8, right: 48, top: 12, bottom: 8, containLabel: true },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      appendToBody: true,
      valueFormatter: function (v) { return v + '%'; }
    },
    xAxis: {
      type: 'value',
      max: 30,
      axisLabel: { formatter: '{value}%', color: muted },
      axisLine: { lineStyle: { color: rule } },
      splitLine: { lineStyle: { color: rule } }
    },
    yAxis: {
      type: 'category',
      data: labels,
      axisLabel: { color: ink, fontSize: 12 },
      axisLine: { lineStyle: { color: rule } },
      axisTick: { show: false }
    },
    series: [{
      type: 'bar',
      data: values,
      barWidth: '54%',
      itemStyle: {
        borderRadius: [0, 6, 6, 0],
        color: {
          type: 'linear', x: 0, y: 0, x2: 1, y2: 0,
          colorStops: [
            { offset: 0, color: accent + '99' },
            { offset: 1, color: accent }
          ]
        }
      },
      label: {
        show: true,
        position: 'right',
        formatter: '{c}%',
        color: accent,
        fontWeight: 700
      }
    }]
  });

  window.addEventListener('resize', function () { chart.resize(); });
})();
