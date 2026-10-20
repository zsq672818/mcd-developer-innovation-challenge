/* AI 知识库办公平台 · 开发计划 —— 图表脚本 */
(function () {
  function cssVar(name, fallback) {
    var v = getComputedStyle(document.documentElement).getPropertyValue(name);
    return (v && v.trim()) || fallback;
  }

  var phases = [
    "阶段 0 · 脚手架",
    "阶段 1 · 数据底座",
    "阶段 2 · 知识库/RAG",
    "阶段 3 · 任务梳理",
    "阶段 4 · 综合看板",
    "阶段 5 · 文档/PPT",
    "阶段 6 · 流程与分析"
  ];
  var effort = [5, 12, 18, 10, 10, 9, 10];

  function renderEffort() {
    var el = document.getElementById("chart-plan-effort");
    if (!el || typeof echarts === "undefined") return;

    var accent = cssVar("--accent", "#3a57e8");
    var accent2 = cssVar("--accent2", "#0e9e8e");
    var ink = cssVar("--ink", "#15171c");
    var muted = cssVar("--muted", "#636a76");
    var rule = cssVar("--rule", "#e3e6eb");
    var bg2 = cssVar("--bg2", "#f5f6f8");
    var fontFamily = cssVar("--sans", "Instrument Sans, sans-serif");

    // 阶段 0–4 属 P0，5–6 属 P1；用两档色彩区分
    var colors = effort.map(function (_, i) {
      return i <= 4 ? accent : accent2;
    });

    var chart = echarts.init(el, null, { renderer: "canvas" });
    chart.setOption({
      grid: { left: 8, right: 48, top: 16, bottom: 8, containLabel: true },
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "shadow" },
        formatter: function (p) {
          var it = p[0];
          return it.name + "<br/>估算工作量：" + it.value + " 人日";
        },
        textStyle: { fontFamily: fontFamily }
      },
      xAxis: {
        type: "value",
        name: "人日",
        nameTextStyle: { color: muted, fontFamily: fontFamily, fontSize: 11 },
        axisLine: { lineStyle: { color: rule } },
        axisLabel: { color: muted, fontFamily: fontFamily, fontSize: 11 },
        splitLine: { lineStyle: { color: rule, type: "dashed" } }
      },
      yAxis: {
        type: "category",
        inverse: true,
        data: phases,
        axisLine: { lineStyle: { color: rule } },
        axisTick: { show: false },
        axisLabel: { color: ink, fontFamily: fontFamily, fontSize: 12 }
      },
      series: [
        {
          type: "bar",
          data: effort.map(function (v, i) {
            return { value: v, itemStyle: { color: colors[i], borderRadius: [0, 4, 4, 0] } };
          }),
          barWidth: "52%",
          label: {
            show: true,
            position: "right",
            formatter: "{c}",
            color: muted,
            fontFamily: fontFamily,
            fontSize: 11,
            fontWeight: 700
          }
        }
      ],
      animationDuration: 700,
      animationEasing: "cubicOut"
    });

    window.addEventListener("resize", function () { chart.resize(); });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", renderEffort);
  } else {
    renderEffort();
  }
})();
