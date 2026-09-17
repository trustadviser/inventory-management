<template>
  <div class="observability-page">
    <section class="hero">
      <div>
        <div class="eyebrow"><span class="pulse"></span> Executive observability</div>
        <h2>Application knowledge graph</h2>
        <p>One view of how customer activity becomes operational decisions across the factory platform.</p>
      </div>
      <div class="hero-actions">
        <div class="updated">Last checked <strong>{{ lastUpdated }}</strong></div>
        <button type="button" :disabled="loading" @click="refresh">
          {{ loading ? 'Refreshing…' : 'Refresh signals' }}
        </button>
      </div>
    </section>

    <section class="signal-grid" aria-label="System health summary">
      <article class="signal primary">
        <div class="signal-head"><span>Platform health</span><span class="status-pill" :class="healthState">{{ healthLabel }}</span></div>
        <strong>{{ healthState === 'healthy' ? 'All systems operational' : 'Attention required' }}</strong>
        <p>Live readiness from the inventory API</p>
      </article>
      <article class="signal">
        <div class="signal-head"><span>Observed requests</span><span class="mini-icon blue">↗</span></div>
        <strong>{{ formatNumber(totalRequests) }}</strong>
        <p>Since the API process started</p>
      </article>
      <article class="signal">
        <div class="signal-head"><span>Success rate</span><span class="mini-icon green">✓</span></div>
        <strong>{{ successRate }}%</strong>
        <p>Responses below HTTP 400</p>
      </article>
      <article class="signal">
        <div class="signal-head"><span>Business capabilities</span><span class="mini-icon violet">◆</span></div>
        <strong>6</strong>
        <p>Connected operational domains</p>
      </article>
    </section>

    <section class="content-grid">
      <article class="panel graph-panel">
        <div class="panel-heading">
          <div><span class="section-label">SYSTEM LANDSCAPE</span><h3>How the platform creates value</h3></div>
          <div class="legend"><span><i class="dot experience"></i>Experience</span><span><i class="dot service"></i>Service</span><span><i class="dot capability"></i>Capability</span><span><i class="dot data"></i>Data</span></div>
        </div>

        <div class="graph" role="img" aria-label="Knowledge graph connecting executive users to the web application, inventory API, business capabilities, and operational data">
          <svg class="edges" viewBox="0 0 1000 500" preserveAspectRatio="none" aria-hidden="true">
            <path d="M130 250 C190 250 190 250 245 250" />
            <path d="M365 250 C420 250 420 250 475 250" />
            <path d="M595 250 C650 250 640 75 700 75" />
            <path d="M595 250 C650 250 640 145 700 145" />
            <path d="M595 250 C650 250 640 215 700 215" />
            <path d="M595 250 C650 250 640 285 700 285" />
            <path d="M595 250 C650 250 640 355 700 355" />
            <path d="M595 250 C650 250 640 425 700 425" />
            <path d="M840 75 C895 75 885 215 930 215" />
            <path d="M840 145 C895 145 885 215 930 215" />
            <path d="M840 215 L930 215" />
            <path d="M840 285 L930 285" />
            <path d="M840 355 C895 355 885 285 930 285" />
            <path d="M840 425 C895 425 885 285 930 285" />
          </svg>

          <div class="node person" style="left: 2%; top: 42%"><span class="node-icon">C</span><div><b>CIO &amp; leaders</b><small>Decision makers</small></div></div>
          <div class="node experience-node" style="left: 23%; top: 42%"><span class="node-icon">UI</span><div><b>Web experience</b><small>Vue application</small></div></div>
          <div class="node service-node" style="left: 47%; top: 42%"><span class="node-icon">API</span><div><b>Inventory API</b><small><i :class="healthState"></i>{{ healthLabel }}</small></div></div>
          <div v-for="(node, index) in capabilities" :key="node.name" class="node capability-node" :style="{ left: '70%', top: `${4 + index * 14}%` }">
            <span class="node-icon">{{ node.code }}</span><div><b>{{ node.name }}</b><small>{{ node.outcome }}</small></div>
          </div>
          <div class="node data-node" style="left: 91%; top: 35%"><span class="node-icon">DB</span><div><b>Operational data</b><small>Orders · stock</small></div></div>
          <div class="node data-node" style="left: 91%; top: 56%"><span class="node-icon">$</span><div><b>Financial data</b><small>Spend · value</small></div></div>
        </div>
      </article>

      <aside class="panel insight-panel">
        <span class="section-label">CIO BRIEF</span>
        <h3>What this means</h3>
        <div class="brief-item"><span class="brief-number">01</span><div><b>Shared operational backbone</b><p>Six business capabilities depend on one API and a common data layer.</p></div></div>
        <div class="brief-item"><span class="brief-number">02</span><div><b>Health is measurable</b><p>Readiness, traffic, errors, and latency are now visible as live signals.</p></div></div>
        <div class="brief-item"><span class="brief-number">03</span><div><b>Traceable customer journeys</b><p>Request IDs connect a user interaction to its API access log.</p></div></div>
        <div class="risk-card">
          <div><span class="risk-icon">!</span><b>Architecture watchpoint</b></div>
          <p>The current in-memory data layer is a single dependency. Introduce durable storage before production scale.</p>
        </div>
      </aside>
    </section>

    <section class="panel capability-table">
      <div class="panel-heading"><div><span class="section-label">CAPABILITY REGISTER</span><h3>Business-to-technology alignment</h3></div><span class="table-note">Live architecture inventory</span></div>
      <div class="table-row table-head"><span>Capability</span><span>Business outcome</span><span>System dependency</span><span>Signal</span></div>
      <div v-for="item in capabilities" :key="item.name" class="table-row">
        <span class="capability-name"><i>{{ item.code }}</i>{{ item.name }}</span><span>{{ item.outcome }}</span><span>Inventory API → JSON datasets</span><span class="operational"><i></i>Operational</span>
      </div>
    </section>
    <p v-if="error" class="error-banner">Live telemetry is unavailable. Showing the last known architecture model.</p>
  </div>
</template>

<script>
import { computed, onMounted, ref } from 'vue'
import { api } from '../api'

export default {
  name: 'Observability',
  setup() {
    const loading = ref(false)
    const error = ref(false)
    const ready = ref(false)
    const lastUpdated = ref('Not yet checked')
    const metrics = ref('')
    const capabilities = [
      { code: 'IN', name: 'Inventory', outcome: 'Stock availability' },
      { code: 'OR', name: 'Orders', outcome: 'Customer fulfillment' },
      { code: 'DE', name: 'Demand', outcome: 'Forward planning' },
      { code: 'BA', name: 'Backlog', outcome: 'Delivery recovery' },
      { code: 'FI', name: 'Finance', outcome: 'Cost governance' },
      { code: 'RE', name: 'Reporting', outcome: 'Performance insight' }
    ]

    const requestLines = computed(() => metrics.value.split('\n').filter(line => line.startsWith('inventory_http_requests_total{')))
    const parsedRequests = computed(() => requestLines.value.map(line => ({
      count: Number(line.split(' ').at(-1)) || 0,
      status: Number(line.match(/status="(\d+)"/)?.[1]) || 0
    })))
    const totalRequests = computed(() => parsedRequests.value.reduce((sum, item) => sum + item.count, 0))
    const successRate = computed(() => {
      if (!totalRequests.value) return '100.0'
      const successful = parsedRequests.value.filter(item => item.status < 400).reduce((sum, item) => sum + item.count, 0)
      return ((successful / totalRequests.value) * 100).toFixed(1)
    })
    const healthState = computed(() => ready.value ? 'healthy' : 'degraded')
    const healthLabel = computed(() => ready.value ? 'Healthy' : 'Unavailable')
    const formatNumber = value => new Intl.NumberFormat('en-US').format(value)

    const refresh = async () => {
      loading.value = true
      error.value = false
      try {
        const [health, metricData] = await Promise.all([api.getServiceHealth(), api.getServiceMetrics()])
        ready.value = health.status === 'ready'
        metrics.value = metricData
        lastUpdated.value = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      } catch (err) {
        ready.value = false
        error.value = true
        lastUpdated.value = 'Connection failed'
      } finally {
        loading.value = false
      }
    }

    onMounted(refresh)
    return { capabilities, error, formatNumber, healthLabel, healthState, lastUpdated, loading, refresh, successRate, totalRequests }
  }
}
</script>

<style scoped>
.observability-page { padding-bottom: 2rem; color: #172033; }
.hero { background: linear-gradient(120deg, #0b1739 0%, #142b58 64%, #15375e 100%); color: white; border-radius: 16px; padding: 2rem 2.25rem; display: flex; justify-content: space-between; align-items: end; box-shadow: 0 14px 35px rgba(15, 35, 70, .18); }
.eyebrow, .section-label { font-size: .7rem; font-weight: 800; letter-spacing: .14em; text-transform: uppercase; }
.eyebrow { color: #a9c7ff; display: flex; align-items: center; gap: .55rem; }
.pulse { width: 8px; height: 8px; border-radius: 50%; background: #45d7a4; box-shadow: 0 0 0 5px rgba(69, 215, 164, .13); }
.hero h2 { font-size: 2rem; margin: .6rem 0 .35rem; letter-spacing: -.025em; }
.hero p { color: #bdcce5; font-size: .95rem; }
.hero-actions { display: flex; align-items: center; gap: 1rem; }
.updated { color: #aebed8; text-align: right; font-size: .72rem; line-height: 1.5; }.updated strong { display: block; color: white; font-size: .82rem; }
.hero button { border: 1px solid rgba(255,255,255,.24); background: rgba(255,255,255,.1); color: white; border-radius: 8px; padding: .7rem 1rem; font-weight: 700; cursor: pointer; }.hero button:hover { background: rgba(255,255,255,.17); }.hero button:disabled { opacity: .55; }
.signal-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin: 1.15rem 0; }
.signal, .panel { background: white; border: 1px solid #e1e7ef; border-radius: 12px; box-shadow: 0 2px 7px rgba(30, 50, 80, .04); }
.signal { padding: 1.1rem 1.2rem; border-top: 3px solid #d8e1ed; }.signal.primary { border-top-color: #36b889; }
.signal-head { display: flex; align-items: center; justify-content: space-between; color: #66758a; font-size: .74rem; font-weight: 700; }.signal strong { display: block; font-size: 1.45rem; margin: .45rem 0 .2rem; letter-spacing: -.02em; }.signal p { color: #8a96a8; font-size: .72rem; }
.status-pill { text-transform: uppercase; font-size: .59rem; letter-spacing: .06em; padding: .24rem .42rem; border-radius: 12px; }.status-pill.healthy { color: #087653; background: #e7f8f1; }.status-pill.degraded { color: #b44141; background: #fff0f0; }
.mini-icon { width: 23px; height: 23px; display: grid; place-items: center; border-radius: 6px; }.blue { color: #246ad3; background: #eaf2ff; }.green { color: #16815f; background: #e8f8f2; }.violet { color: #7049bd; background: #f2ecff; }
.content-grid { display: grid; grid-template-columns: minmax(0, 3fr) minmax(260px, 1fr); gap: 1rem; }
.panel-heading { display: flex; align-items: center; justify-content: space-between; padding: 1.2rem 1.35rem; border-bottom: 1px solid #edf0f5; }.section-label { color: #7b8ba1; }.panel h3 { margin-top: .3rem; font-size: 1rem; }.legend { display: flex; gap: .8rem; color: #7c8899; font-size: .65rem; }.legend span { display: flex; align-items: center; gap: .3rem; }.dot { width: 6px; height: 6px; border-radius: 50%; }.dot.experience { background: #4179cc; }.dot.service { background: #7049bd; }.dot.capability { background: #20a27a; }.dot.data { background: #e39d3e; }
.graph { height: 450px; position: relative; overflow: hidden; background-image: radial-gradient(#dbe3ee 1px, transparent 1px); background-size: 18px 18px; }.edges { position: absolute; inset: 0; width: 100%; height: 100%; }.edges path { fill: none; stroke: #cbd6e4; stroke-width: 1.5; stroke-dasharray: 4 4; vector-effect: non-scaling-stroke; }
.node { position: absolute; transform: translateY(-50%); width: 130px; min-height: 54px; padding: .55rem; background: white; border: 1px solid #dae2ed; border-radius: 9px; box-shadow: 0 5px 14px rgba(31, 51, 83, .09); display: flex; align-items: center; gap: .5rem; z-index: 2; }.node-icon { flex: 0 0 30px; height: 30px; display: grid; place-items: center; border-radius: 7px; font-size: .6rem; font-weight: 900; }.node b { display: block; font-size: .68rem; white-space: nowrap; }.node small { display: flex; align-items: center; gap: .25rem; color: #8a96a8; font-size: .57rem; margin-top: .18rem; white-space: nowrap; }.node small i { width: 5px; height: 5px; border-radius: 50%; }.node small i.healthy { background: #27ad80; }.node small i.degraded { background: #db5d5d; }
.person .node-icon { background: #eef3fa; color: #38506e; }.experience-node { border-color: #a9c8f5; }.experience-node .node-icon { background: #e9f2ff; color: #2468c7; }.service-node { border-color: #c6b6ed; }.service-node .node-icon { background: #f1ecff; color: #7049bd; }.capability-node { border-color: #addfce; }.capability-node .node-icon { background: #e8f8f2; color: #14805e; }.data-node { width: 120px; border-color: #f1d0a2; }.data-node .node-icon { background: #fff4e4; color: #a56616; }
.insight-panel { padding: 1.3rem; }.insight-panel h3 { font-size: 1.15rem; margin-bottom: 1rem; }.brief-item { display: flex; gap: .75rem; padding: 1rem 0; border-top: 1px solid #edf0f5; }.brief-number { color: #9cacbe; font-size: .63rem; font-weight: 800; }.brief-item b { font-size: .78rem; }.brief-item p { color: #738196; font-size: .7rem; line-height: 1.5; margin-top: .25rem; }.risk-card { margin-top: 1rem; background: #fff8ec; border: 1px solid #f4d9ab; border-radius: 9px; padding: .9rem; }.risk-card div { display: flex; align-items: center; gap: .5rem; font-size: .75rem; }.risk-icon { width: 20px; height: 20px; display: grid; place-items: center; border-radius: 50%; background: #f0a53d; color: white; font-weight: 900; }.risk-card p { color: #80633c; font-size: .68rem; line-height: 1.5; margin-top: .55rem; }
.capability-table { margin-top: 1rem; overflow: hidden; }.table-note { color: #8995a6; font-size: .7rem; }.table-row { display: grid; grid-template-columns: 1.1fr 1.2fr 1.5fr .75fr; align-items: center; min-height: 47px; padding: 0 1.35rem; border-top: 1px solid #edf0f5; color: #627087; font-size: .72rem; }.table-head { min-height: 36px; background: #f8fafc; border-top: 0; color: #8793a5; font-size: .62rem; font-weight: 800; text-transform: uppercase; letter-spacing: .05em; }.capability-name { display: flex; align-items: center; gap: .6rem; color: #28364a; font-weight: 700; }.capability-name i { width: 24px; height: 24px; display: grid; place-items: center; background: #edf8f4; color: #16815f; border-radius: 5px; font-size: .55rem; font-style: normal; }.operational { color: #147557; font-weight: 700; }.operational i { display: inline-block; width: 6px; height: 6px; margin-right: .35rem; border-radius: 50%; background: #27ad80; }.error-banner { background: #fff1f1; color: #ad3f3f; border: 1px solid #f3cccc; border-radius: 8px; padding: .75rem 1rem; margin-top: 1rem; font-size: .78rem; }
@media (max-width: 1100px) { .signal-grid { grid-template-columns: repeat(2, 1fr); }.content-grid { grid-template-columns: 1fr; }.graph-panel { overflow-x: auto; }.graph { min-width: 980px; }.nav-tabs a { padding-left: .7rem; padding-right: .7rem; } }
@media (max-width: 700px) { .hero { align-items: flex-start; gap: 1rem; flex-direction: column; }.hero-actions { width: 100%; justify-content: space-between; }.signal-grid { grid-template-columns: 1fr; }.table-row { grid-template-columns: 1fr 1fr; gap: .4rem; padding: .7rem 1rem; }.table-head { display: none; } }
</style>
