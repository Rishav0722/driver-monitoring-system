from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import datetime

app = FastAPI()

alerts = []

@app.get("/alerts")
def get_alerts():
    return {"alerts": alerts}

@app.post("/alerts")
def add_alert(ear: float):
    alert = {
        "timestamp": str(datetime.datetime.now()),
        "ear": ear
    }
    alerts.append(alert)
    return {"message": "Alert saved", "alert": alert}


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>DMS Live Dashboard</title>
    <style>
        body {
            font-family: -apple-system, Segoe UI, Arial, sans-serif;
            background: #0f172a;
            color: #e2e8f0;
            margin: 0;
            padding: 24px;
        }
        h1 { font-size: 20px; margin-bottom: 4px; }
        .sub { color: #94a3b8; font-size: 13px; margin-bottom: 20px; }
        .card {
            background: #1e293b;
            border-radius: 10px;
            padding: 16px 20px;
            margin-bottom: 20px;
        }
        canvas { width: 100%; height: 160px; }
        table { width: 100%; border-collapse: collapse; font-size: 13px; }
        th, td { text-align: left; padding: 6px 8px; border-bottom: 1px solid #334155; }
        th { color: #94a3b8; font-weight: 500; }
        .low { color: #f87171; font-weight: 600; }
        .ok { color: #4ade80; }
        .empty { color: #64748b; padding: 20px 0; }
    </style>
</head>
<body>
    <h1>Driver Monitoring System — Live Alerts</h1>
    <div class="sub" id="status">Connecting…</div>

    <div class="card">
        <canvas id="earChart"></canvas>
    </div>

    <div class="card">
        <table id="alertTable">
            <thead>
                <tr><th>Time</th><th>EAR</th><th>Status</th></tr>
            </thead>
            <tbody id="alertBody"></tbody>
        </table>
        <div id="emptyMsg" class="empty" style="display:none;">No alerts yet — waiting for data.</div>
    </div>

    <script>
        const EAR_THRESHOLD = 0.25; // adjust to match your dms.py threshold

        async function refresh() {
            try {
                const res = await fetch('/alerts');
                const data = await res.json();
                const alerts = data.alerts || [];
                document.getElementById('status').textContent =
                    alerts.length + ' alert(s) recorded — refreshing every 2s';

                const body = document.getElementById('alertBody');
                const empty = document.getElementById('emptyMsg');
                body.innerHTML = '';

                if (alerts.length === 0) {
                    empty.style.display = 'block';
                } else {
                    empty.style.display = 'none';
                    const recent = alerts.slice(-15).reverse();
                    for (const a of recent) {
                        const tr = document.createElement('tr');
                        const isLow = a.ear < EAR_THRESHOLD;
                        tr.innerHTML =
                            '<td>' + a.timestamp + '</td>' +
                            '<td>' + a.ear.toFixed(3) + '</td>' +
                            '<td class="' + (isLow ? 'low' : 'ok') + '">' +
                            (isLow ? 'Drowsy' : 'Alert') + '</td>';
                        body.appendChild(tr);
                    }
                }

                drawChart(alerts.slice(-40));
            } catch (e) {
                document.getElementById('status').textContent = 'Could not reach API — is it running?';
            }
        }

        function drawChart(alerts) {
            const canvas = document.getElementById('earChart');
            const ctx = canvas.getContext('2d');
            canvas.width = canvas.clientWidth;
            canvas.height = 160;
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            if (alerts.length < 2) return;

            const values = alerts.map(a => a.ear);
            const min = Math.min(...values, EAR_THRESHOLD) - 0.02;
            const max = Math.max(...values) + 0.02;
            const w = canvas.width, h = canvas.height;

            // threshold line
            const ty = h - ((EAR_THRESHOLD - min) / (max - min)) * h;
            ctx.strokeStyle = '#f87171';
            ctx.setLineDash([4, 4]);
            ctx.beginPath();
            ctx.moveTo(0, ty);
            ctx.lineTo(w, ty);
            ctx.stroke();
            ctx.setLineDash([]);

            // EAR line
            ctx.strokeStyle = '#38bdf8';
            ctx.lineWidth = 2;
            ctx.beginPath();
            values.forEach((v, i) => {
                const x = (i / (values.length - 1)) * w;
                const y = h - ((v - min) / (max - min)) * h;
                i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
            });
            ctx.stroke();
        }

        refresh();
        setInterval(refresh, 2000);
    </script>
</body>
</html>
"""
