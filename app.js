/**
 * ═══════════════════════════════════════════════════════════════════
 *  AEROSTAT HMI  ·  app.js
 *  Pure Vanilla JavaScript – no frameworks, no build tools.
 *  Target: 1024 × 600 kiosk display (Raspberry Pi)
 * ═══════════════════════════════════════════════════════════════════
 */

'use strict';

/* ─────────────────────────────────────────────────────────────────
   MODULE: Navigation Controller
   Manages tab switching, screen visibility, and active-state styling.
   ─────────────────────────────────────────────────────────────────── */
const Navigation = (() => {

  /** All bottom-nav tab buttons */
  const tabs = document.querySelectorAll('.nav-tab');

  /** All screen section elements */
  const screens = document.querySelectorAll('.screen');

  /**
   * Activates the requested screen and deactivates all others.
   * @param {string} target  – value of data-target on the clicked tab
   */
  function activateScreen(target) {
    // ── Update screens ──────────────────────────────────────────
    screens.forEach(screen => {
      const isTarget = screen.id === `screen-${target}`;
      screen.classList.toggle('active', isTarget);
      // Screens use display:flex when active (set via .active class → CSS)
      screen.style.display = isTarget ? '' : 'none';
    });

    // ── Update tab highlight ────────────────────────────────────
    tabs.forEach(tab => {
      tab.classList.toggle('active', tab.dataset.target === target);
    });

    // ── Lifecycle hooks ─────────────────────────────────────────
    if (target === 'map' && !MapScreen.initialised) MapScreen.init();
    if (target === 'home') SparklineCharts.resize();
  }

  /** Bind click listeners to every nav tab */
  function init() {
    tabs.forEach(tab => {
      tab.addEventListener('click', () => {
        activateScreen(tab.dataset.target);
      });
    });

    // Ensure only the active screen is visible on load
    screens.forEach(screen => {
      if (!screen.classList.contains('active')) {
        screen.style.display = 'none';
      }
    });
  }

  return { init, activateScreen };
})();


/* ─────────────────────────────────────────────────────────────────
   MODULE: Clock
   Updates the header clock display every second.
   ─────────────────────────────────────────────────────────────────── */
const Clock = (() => {
  const elClock = document.getElementById('hdr-clock');

  function tick() {
    const now  = new Date();
    const hh   = String(now.getHours()).padStart(2, '0');
    const mm   = String(now.getMinutes()).padStart(2, '0');
    elClock.textContent = `${hh}:${mm}`;
  }

  function init() {
    tick();
    setInterval(tick, 5000);
  }

  return { init };
})();


/* ─────────────────────────────────────────────────────────────────
   MODULE: Telemetry Simulation
   Simulates a live hardware data feed by slightly randomising
   Altitude, Wind Speed, and Tether Tension every second.
   Also mirrors the values onto the VIDEO and MAP overlays.
   ─────────────────────────────────────────────────────────────────── */
const Telemetry = (() => {

  // ── Telemetry state ──────────────────────────────────────────────
  const state = {
    altitude: 512.0,   // metres
    tension:   27.8,   // kg
    wind:      12.4,   // m/s
    heading:  247,     // degrees
    speed:     3.2,    // m/s (aerostat drift)
    dbm:      -71,     // dBm signal strength
  };

  // ── DOM refs (HOME screen) ────────────────────────────────────────
  const elAlt     = document.getElementById('val-altitude');
  const elTension = document.getElementById('val-tension');
  const elWind    = document.getElementById('val-wind');
  const elDbm     = document.getElementById('val-dbm');

  // ── DOM refs (VIDEO HUD) ─────────────────────────────────────────
  const elVidAlt     = document.getElementById('vid-alt');
  const elVidWind    = document.getElementById('vid-wind');
  const elVidTension = document.getElementById('vid-tension');
  const elVidHdg     = document.getElementById('vid-heading');

  // ── DOM refs (MAP overlay) ───────────────────────────────────────
  const elMapAlt = document.getElementById('map-alt');
  const elMapSpd = document.getElementById('map-spd');
  const elMapHdg = document.getElementById('map-hdg');

  /**
   * Slightly nudges a value by ±delta with clamping.
   * @param {number} val   – current value
   * @param {number} delta – max random change per tick
   * @param {number} min   – minimum value
   * @param {number} max   – maximum value
   * @param {number} dp    – decimal places for rounding
   */
  function nudge(val, delta, min, max, dp = 1) {
    const next = val + (Math.random() * delta * 2 - delta);
    return parseFloat(Math.min(max, Math.max(min, next)).toFixed(dp));
  }

  /** Pushes latest data to a sparkline dataset, keeping a fixed window. */
  function pushSparkData(chart, value) {
    const data = chart.data.datasets[0].data;
    data.push(value);
    if (data.length > SPARK_WINDOW) data.shift();
    chart.update('none'); // skip animation for performance
  }

  /** Update all display elements from the current state object */
  function updateDOM() {
    // HOME
    elAlt.textContent     = state.altitude.toFixed(0);
    elTension.textContent = state.tension.toFixed(1);
    elWind.textContent    = state.wind.toFixed(1);
    elDbm.textContent     = state.dbm.toFixed(0);

    // VIDEO HUD
    elVidAlt.textContent     = `${state.altitude.toFixed(0)} m`;
    elVidWind.textContent    = `${state.wind.toFixed(1)} m/s`;
    elVidTension.textContent = `${state.tension.toFixed(1)} kg`;
    elVidHdg.textContent     = `${state.heading}°`;

    // MAP
    elMapAlt.textContent = `${state.altitude.toFixed(0)} m`;
    elMapSpd.textContent = `${state.speed.toFixed(1)} m/s`;
    elMapHdg.textContent = `${state.heading}°`;
  }

  /** One simulation tick – called every second */
  function tick() {
    state.altitude = nudge(state.altitude, 2.5, 480, 595, 0);
    state.tension  = nudge(state.tension,  0.4, 22, 32,   1);
    state.wind     = nudge(state.wind,     0.3, 8,  18,   1);
    state.speed    = nudge(state.speed,    0.2, 1,  6,    1);
    state.dbm      = nudge(state.dbm,      1,  -85, -55,  0);
    state.heading  = (state.heading + Math.round(Math.random() * 2 - 1) + 360) % 360;

    updateDOM();

    // Push to sparklines
    if (SparklineCharts.ready) {
      pushSparkData(SparklineCharts.altitude, state.altitude);
      pushSparkData(SparklineCharts.tension,  state.tension);
      pushSparkData(SparklineCharts.wind,     state.wind);
    }
  }

  function init() {
    updateDOM();
    setInterval(tick, 1000);
  }

  return { init, state };
})();


/* ─────────────────────────────────────────────────────────────────
   MODULE: SparklineCharts
   Chart.js sparklines for the three metric panels on HOME.
   ─────────────────────────────────────────────────────────────────── */
const SPARK_WINDOW = 30; // number of data points visible

const SparklineCharts = (() => {

  let altitude = null;
  let tension  = null;
  let wind     = null;
  let ready    = false;

  /** Generates initial sine-wave-ish seed data to fill the chart */
  function seedData(base, amplitude, points) {
    return Array.from({ length: points }, (_, i) =>
      base + Math.sin(i * 0.4) * amplitude + (Math.random() - 0.5) * amplitude * 0.5
    );
  }

  /** Returns a Chart.js sparkline config object */
  function sparklineConfig(data, color) {
    return {
      type: 'line',
      data: {
        labels: Array(data.length).fill(''),
        datasets: [{
          data,
          borderColor:     color,
          borderWidth:     1.5,
          fill:            true,
          backgroundColor: `${color}18`,  // very subtle fill
          pointRadius:     0,
          tension:         0.4,
        }]
      },
      options: {
        responsive:          true,
        maintainAspectRatio: false,
        animation:           false,
        plugins: { legend: { display: false }, tooltip: { enabled: false } },
        scales: {
          x: { display: false },
          y: { display: false, grace: '10%' }
        },
        elements: { line: { capBezierPoints: false } }
      }
    };
  }

  function init() {
    altitude = new Chart(
      document.getElementById('spark-altitude'),
      sparklineConfig(seedData(512, 15, SPARK_WINDOW), '#00FF00')
    );
    tension = new Chart(
      document.getElementById('spark-tension'),
      sparklineConfig(seedData(27.8, 1.5, SPARK_WINDOW), '#00FF00')
    );
    wind = new Chart(
      document.getElementById('spark-wind'),
      sparklineConfig(seedData(12.4, 1.5, SPARK_WINDOW), '#00FF00')
    );
    ready = true;
  }

  /** Trigger chart resize (call when HOME tab becomes active) */
  function resize() {
    [altitude, tension, wind].forEach(c => c && c.resize());
  }

  return { init, resize, get altitude() { return altitude; },
                         get tension()  { return tension;  },
                         get wind()     { return wind;     },
                         get ready()    { return ready;    } };
})();


/* ─────────────────────────────────────────────────────────────────
   MODULE: RecordingTimer
   Simulates a recording counter that increments on VIDEO screen.
   ─────────────────────────────────────────────────────────────────── */
const RecordingTimer = (() => {
  let totalSeconds = 12 * 60 + 34; // 00:12:34 – pre-seeded
  const el = document.getElementById('rec-timer');

  function format(s) {
    const hh = String(Math.floor(s / 3600)).padStart(2, '0');
    const mm = String(Math.floor((s % 3600) / 60)).padStart(2, '0');
    const ss = String(s % 60).padStart(2, '0');
    return `${hh}:${mm}:${ss}`;
  }

  function init() {
    el.textContent = format(totalSeconds);
    setInterval(() => {
      totalSeconds++;
      el.textContent = format(totalSeconds);
    }, 1000);
  }

  return { init };
})();


/* ─────────────────────────────────────────────────────────────────
   MODULE: MapScreen
   Initialises a Leaflet.js map with a dark tile layer,
   custom ground-station and aerostat markers, and a tether line.
   Zoom buttons wire up to Leaflet's native zoom API.
   ─────────────────────────────────────────────────────────────────── */
const MapScreen = (() => {
  let map         = null;
  let aerosatMkr  = null;
  let tetherLine  = null;
  let initialised = false;

  // Fixed ground-station coordinates (New Delhi area – example)
  const GROUND_COORD = [28.608, 77.202];
  // Aerostat starts NE of ground station
  const AEROSTAT_COORD = [28.618, 77.218];

  /** Create a custom HTML Leaflet icon */
  function makeIcon(svgHTML, labelText) {
    const div = document.createElement('div');
    div.style.cssText = 'display:flex;flex-direction:column;align-items:center;gap:3px;';

    const svgEl = document.createElement('div');
    svgEl.innerHTML = svgHTML;
    svgEl.style.cssText = 'filter:drop-shadow(0 0 6px rgba(0,229,255,0.8));';

    const lbl = document.createElement('div');
    lbl.className = 'map-marker-label';
    lbl.textContent = labelText;

    div.appendChild(svgEl);
    div.appendChild(lbl);

    return L.divIcon({
      html:        div.outerHTML,
      className:   '',
      iconSize:    [80, 50],
      iconAnchor:  [40, 14],
    });
  }

  const GROUND_SVG = `<svg width="24" height="24" viewBox="0 0 24 24" fill="none">
    <rect x="2" y="14" width="20" height="8" rx="2" fill="#00E5FF" opacity="0.3" stroke="#00E5FF" stroke-width="1.5"/>
    <line x1="12" y1="14" x2="12" y2="4" stroke="#00E5FF" stroke-width="1.8" stroke-linecap="round"/>
    <line x1="8"  y1="8"  x2="16" y2="8" stroke="#00E5FF" stroke-width="1.4"/>
    <line x1="6"  y1="6"  x2="12" y2="4" stroke="#00E5FF" stroke-width="1.2"/>
    <line x1="18" y1="6"  x2="12" y2="4" stroke="#00E5FF" stroke-width="1.2"/>
  </svg>`;

  const AEROSTAT_SVG = `<svg width="24" height="24" viewBox="0 0 24 24" fill="none">
    <ellipse cx="12" cy="8" rx="7" ry="9" fill="#00E5FF" opacity="0.25" stroke="#00E5FF" stroke-width="1.5"/>
    <ellipse cx="12" cy="8" rx="4" ry="5" fill="#00E5FF" opacity="0.2"/>
    <line x1="12" y1="17" x2="12" y2="22" stroke="#00E5FF" stroke-width="1.5" stroke-linecap="round"/>
    <line x1="9"  y1="20" x2="15" y2="20" stroke="#00E5FF" stroke-width="1.2" stroke-linecap="round"/>
  </svg>`;

  function init() {
    if (initialised) return;
    initialised = true;

    // ── Create Leaflet map ─────────────────────────────────────
    map = L.map('map-container', {
      center:       GROUND_COORD,
      zoom:         15,
      zoomControl:  false,
      attributionControl: false,
      dragging:     false,   // locked in kiosk mode
      scrollWheelZoom: false,
    });

    // Dark satellite-style tile (OpenStreetMap with no extra key needed)
    // Using CartoDB dark-matter for a tactical dark look
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      maxZoom: 19,
      subdomains: 'abcd',
    }).addTo(map);

    // ── Tether line ────────────────────────────────────────────
    tetherLine = L.polyline([GROUND_COORD, AEROSTAT_COORD], {
      color:  '#00E5FF',
      weight: 2,
      opacity: 0.7,
      dashArray: '6 4',
    }).addTo(map);

    // ── Ground station marker ──────────────────────────────────
    L.marker(GROUND_COORD, {
      icon: makeIcon(GROUND_SVG, 'GROUND STATION'),
    }).addTo(map);

    // ── Aerostat marker ────────────────────────────────────────
    aerosatMkr = L.marker(AEROSTAT_COORD, {
      icon: makeIcon(AEROSTAT_SVG, 'AEROSTAT'),
    }).addTo(map);

    // Force tile load after the container becomes visible
    setTimeout(() => map.invalidateSize(), 120);

    // ── Wire up custom zoom buttons ────────────────────────────
    document.getElementById('btn-zoom-in').addEventListener('click', () => {
      map.zoomIn(1);
    });
    document.getElementById('btn-zoom-out').addEventListener('click', () => {
      map.zoomOut(1);
    });
  }

  return { init, get initialised() { return initialised; } };
})();


/* ─────────────────────────────────────────────────────────────────
   MODULE: VideoControls
   Handles snapshot flash and record-mode toggle.
   ─────────────────────────────────────────────────────────────────── */
const VideoControls = (() => {

  let recording = true; // pre-seeded as recording

  function showToast(msg) {
    let toast = document.querySelector('.toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.className = 'toast';
      document.body.appendChild(toast);
    }
    toast.textContent = msg;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 2200);
  }

  function init() {
    // Snapshot
    document.getElementById('btn-snapshot').addEventListener('click', () => {
      // Flash the screen briefly to simulate a snapshot
      const flash = document.createElement('div');
      flash.style.cssText = `
        position:fixed;inset:0;background:#fff;opacity:0.5;z-index:999;
        pointer-events:none;transition:opacity 0.4s;
      `;
      document.body.appendChild(flash);
      requestAnimationFrame(() => {
        flash.style.opacity = '0';
        setTimeout(() => flash.remove(), 500);
      });
      showToast('📸  SNAPSHOT SAVED');
    });

    // Record toggle
    const btnRecord = document.getElementById('btn-record');
    const recDot    = document.querySelector('.rec-dot');

    btnRecord.addEventListener('click', () => {
      recording = !recording;
      if (recording) {
        recDot.style.animationPlayState = 'running';
        showToast('⏺  RECORDING STARTED');
      } else {
        recDot.style.animationPlayState = 'paused';
        recDot.style.opacity = '0.3';
        showToast('⏹  RECORDING STOPPED');
      }
    });

    // Fullscreen
    document.getElementById('btn-fullscreen').addEventListener('click', () => {
      if (document.fullscreenElement) {
        document.exitFullscreen();
      } else {
        document.documentElement.requestFullscreen().catch(() => {
          showToast('Fullscreen not available');
        });
      }
    });
  }

  return { init };
})();


/* ─────────────────────────────────────────────────────────────────
   MODULE: SettingsControls
   Shutdown modal, settings button feedback.
   ─────────────────────────────────────────────────────────────────── */
const SettingsControls = (() => {
  const modal         = document.getElementById('shutdown-modal');
  const btnShutdown   = document.getElementById('sbtn-shutdown');
  const btnCancel     = document.getElementById('btn-shutdown-cancel');
  const btnConfirm    = document.getElementById('btn-shutdown-confirm');

  function showToast(msg) {
    let toast = document.querySelector('.toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.className = 'toast';
      document.body.appendChild(toast);
    }
    toast.textContent = msg;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 2200);
  }

  function init() {
    btnShutdown.addEventListener('click', () => {
      modal.classList.remove('hidden');
    });
    btnCancel.addEventListener('click', () => {
      modal.classList.add('hidden');
    });
    btnConfirm.addEventListener('click', () => {
      modal.classList.add('hidden');
      // Simulate shutdown: black out screen
      document.body.style.transition = 'opacity 1s';
      document.body.style.opacity    = '0';
      setTimeout(() => {
        document.body.innerHTML =
          '<div style="display:flex;height:100vh;align-items:center;justify-content:center;' +
          'background:#000;color:#333;font-family:monospace;font-size:14px;letter-spacing:0.1em;">' +
          'SYSTEM SHUTDOWN</div>';
        document.body.style.opacity = '1';
      }, 1200);
    });

    // Provide haptic-style visual feedback for non-shutdown buttons
    ['sbtn-mission','sbtn-camera','sbtn-radio','sbtn-display',
     'sbtn-system','sbtn-calibration','sbtn-info'].forEach(id => {
      const btn = document.getElementById(id);
      if (btn) {
        btn.addEventListener('click', () => {
          showToast(`${btn.querySelector('span').textContent} – not implemented in demo`);
        });
      }
    });
  }

  return { init };
})();


/* ─────────────────────────────────────────────────────────────────
   MODULE: HamburgerMenu
   Simple visual feedback (kiosk devices typically have no sidebar).
   ─────────────────────────────────────────────────────────────────── */
function initHamburger() {
  document.getElementById('btn-hamburger').addEventListener('click', () => {
    // In a real deployment this could slide in a system panel
    const toast = document.querySelector('.toast') || (() => {
      const t = document.createElement('div');
      t.className = 'toast';
      document.body.appendChild(t);
      return t;
    })();
    toast.textContent = 'MENU – not implemented in demo';
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 2000);
  });
}


/* ─────────────────────────────────────────────────────────────────
   MODULE: BatteryIndicator
   Slowly decrements battery % to show live drain.
   ─────────────────────────────────────────────────────────────────── */
const BatteryIndicator = (() => {
  let pct       = 89;
  const elFill  = document.getElementById('battery-fill');
  const elPctOv = document.getElementById('battery-pct-overlay');
  const elHdrPct = document.getElementById('hdr-battery-pct');

  function update() {
    elFill.style.width    = `${pct}%`;
    elPctOv.textContent   = `${pct}%`;
    elHdrPct.textContent  = `${pct}%`;

    // Colour shift: green → amber → red
    if (pct > 50) {
      elFill.style.background = 'linear-gradient(90deg,#00c846,#00FF00)';
    } else if (pct > 20) {
      elFill.style.background = 'linear-gradient(90deg,#c8a200,#FFB300)';
    } else {
      elFill.style.background = 'linear-gradient(90deg,#c80000,#FF3333)';
    }
  }

  function init() {
    update();
    // Drain 1% every 60 seconds (simulated)
    setInterval(() => {
      if (pct > 1) { pct -= 1; update(); }
    }, 60000);
  }

  return { init };
})();


/* ─────────────────────────────────────────────────────────────────
   MODULE: CameraPlayer
   Connects to go2rtc via WebRTC and renders the CEZR10 live feed
   into the <video#camera-feed> element.
   Auto-reconnects every 5 seconds if the stream drops.

   go2rtc must be running on the Raspberry Pi:
     ./go2rtc -config go2rtc.yaml
   It listens on http://localhost:1984  by default.
   ─────────────────────────────────────────────────────────────────── */
const CameraPlayer = (() => {

  // ── Config ─────────────────────────────────────────────────────
  // When running ON the Raspberry Pi, localhost works.
  // If accessing from another device on the same LAN, replace with
  // the Pi's IP address, e.g. 'http://192.168.1.100:1984'
  const GO2RTC_BASE   = `http://${window.location.hostname}:1984`;
  const STREAM_NAME   = 'aerostat_cam';   // must match go2rtc.yaml
  const RECONNECT_MS  = 5000;            // retry interval

  // ── DOM refs ───────────────────────────────────────────────────
  const videoEl      = document.getElementById('camera-feed');
  const videoHomeEl  = document.getElementById('camera-feed-home');
  const payloadSvgEl = document.getElementById('payload-cam-svg');
  const payloadLabel = document.getElementById('payload-status-label');
  const offlineEl    = document.getElementById('stream-offline');
  const statusMsg    = document.getElementById('stream-status-msg');

  let pc             = null;   // RTCPeerConnection
  let reconnectTimer = null;
  let alive          = false;  // true when stream is flowing

  /** Show/hide the offline overlay */
  function setLive(isLive) {
    alive = isLive;
    videoEl.classList.toggle('live', isLive);
    offlineEl.classList.toggle('hidden', isLive);
    
    if (videoHomeEl) {
      videoHomeEl.style.opacity = isLive ? '1' : '0';
      if (payloadSvgEl) payloadSvgEl.style.opacity = isLive ? '0' : '1';
      if (payloadLabel) {
        payloadLabel.textContent = isLive ? '● ACTIVE' : '● STANDBY';
        payloadLabel.className = isLive ? 'panel-sub-label green' : 'panel-sub-label red';
      }
    }
  }

  /** Clean up an existing peer connection */
  function closePeer() {
    if (pc) {
      pc.close();
      pc = null;
    }
  }

  /**
   * Negotiate WebRTC with go2rtc.
   * go2rtc exposes a simple WHEP-like endpoint:
   *   POST /api/webrtc?src=<stream_name>
   * with an SDP offer body → returns SDP answer.
   */
  async function connect() {
    statusMsg.textContent = 'Connecting to camera…';
    closePeer();

    try {
      pc = new RTCPeerConnection({
        iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
      });

      // We only receive — tell the peer connection to expect video (+ audio)
      pc.addTransceiver('video', { direction: 'recvonly' });
      pc.addTransceiver('audio', { direction: 'recvonly' });

      // Wire the incoming video track to the <video> element
      pc.ontrack = (evt) => {
        if (evt.track.kind === 'video') {
          const stream = evt.streams[0];
          videoEl.srcObject = stream;
          if (videoHomeEl) videoHomeEl.srcObject = stream;
          
          videoEl.play().then(() => {
            if (videoHomeEl) videoHomeEl.play().catch(console.warn);
            setLive(true);
            console.log('[CameraPlayer] Stream live ✓');
          }).catch(console.warn);
        }
      };

      // Reconnect if ICE fails
      pc.oniceconnectionstatechange = () => {
        if (['disconnected','failed','closed'].includes(pc.iceConnectionState)) {
          console.warn('[CameraPlayer] ICE state:', pc.iceConnectionState);
          scheduleReconnect();
        }
      };

      // Create SDP offer
      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);

      // Send to go2rtc, receive answer
      const resp = await fetch(
        `${GO2RTC_BASE}/api/webrtc?src=${STREAM_NAME}`,
        {
          method:  'POST',
          headers: { 'Content-Type': 'application/sdp' },
          body:    pc.localDescription.sdp,
        }
      );

      if (!resp.ok) throw new Error(`go2rtc HTTP ${resp.status}`);

      const answerSDP = await resp.text();
      await pc.setRemoteDescription({ type: 'answer', sdp: answerSDP });

      statusMsg.textContent = 'Stream connected — waiting for frame…';

    } catch (err) {
      console.warn('[CameraPlayer] Connect error:', err.message);
      statusMsg.textContent = `Offline · retrying in ${RECONNECT_MS / 1000}s…`;
      setLive(false);
      scheduleReconnect();
    }
  }

  function scheduleReconnect() {
    closePeer();
    setLive(false);
    clearTimeout(reconnectTimer);
    reconnectTimer = setTimeout(() => connect(), RECONNECT_MS);
  }

  function init() {
    // Show offline overlay immediately on page load
    setLive(false);
    // Attempt first connection
    connect();
  }

  return { init };
})();





/* ─────────────────────────────────────────────────────────────────
   BOOT SEQUENCE  –  called once the DOM is ready
   ─────────────────────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {

  // 1. Navigation controller (must be first)
  Navigation.init();

  // 2. Live clock
  Clock.init();

  // 3. Sparkline charts (HOME panels)
  SparklineCharts.init();

  // 4. Telemetry data feed (seeds charts + all overlays)
  Telemetry.init();

  // 5. Recording timer (VIDEO screen)
  RecordingTimer.init();

  // 6. Camera controls (VIDEO screen)
  VideoControls.init();

  // 7. Settings & shutdown (SETTINGS screen)
  SettingsControls.init();

  // 8. Battery display
  BatteryIndicator.init();

  // 9. Hamburger placeholder
  initHamburger();

  // 10. Map is lazy-initialised on first visit to the MAP tab
  //     (see MapScreen.init() called from Navigation.activateScreen)

  // 11. WebRTC camera player — connects to go2rtc on port 1984
  //     Will show "STREAM OFFLINE" until go2rtc + camera are running.
  CameraPlayer.init();


  console.log('[AEROSTAT HMI] Boot complete. All modules active.');
});
