from datetime import datetime
from ..models import Finding, ScanResult

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GitShodanKey Report</title>
<style>
  :root { --bg: #0d1117; --surface: #161b22; --border: #30363d; --text: #c9d1d9; --muted: #8b949e; --green: #3fb950; --red: #f85149; --yellow: #d29922; --blue: #58a6ff; }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--text); font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', monospace; padding: 2rem; }
  h1 { color: var(--blue); font-size: 1.8rem; margin-bottom: 0.25rem; }
  .subtitle { color: var(--muted); margin-bottom: 2rem; font-size: 0.9rem; }
  .stats { display: flex; gap: 1rem; margin-bottom: 2rem; flex-wrap: wrap; }
  .stat { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1rem 1.5rem; min-width: 140px; }
  .stat .label { color: var(--muted); font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; }
  .stat .value { font-size: 2rem; font-weight: bold; margin-top: 0.25rem; }
  .stat.green .value { color: var(--green); }
  .stat.blue .value { color: var(--blue); }
  .stat.yellow .value { color: var(--yellow); }
  table { width: 100%; border-collapse: collapse; background: var(--surface); border-radius: 8px; overflow: hidden; border: 1px solid var(--border); }
  thead { background: #1c2128; }
  th { padding: 0.75rem 1rem; text-align: left; color: var(--muted); font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 1px solid var(--border); }
  td { padding: 0.75rem 1rem; border-bottom: 1px solid var(--border); font-size: 0.875rem; vertical-align: top; }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: rgba(255,255,255,0.03); }
  .badge { display: inline-block; padding: 0.15rem 0.5rem; border-radius: 12px; font-size: 0.75rem; font-weight: 600; }
  .badge.valid { background: rgba(63,185,80,0.15); color: var(--green); }
  .badge.invalid { background: rgba(248,81,73,0.15); color: var(--red); }
  .service-badge { background: rgba(88,166,255,0.15); color: var(--blue); }
  .key { font-family: monospace; font-size: 0.8rem; color: var(--yellow); }
  a { color: var(--blue); text-decoration: none; }
  a:hover { text-decoration: underline; }
  .credits { color: var(--green); font-size: 0.8rem; }
</style>
</head>
<body>
<h1>🔑 GitShodanKey Report</h1>
<div class="subtitle">Generated: {{ timestamp }} | Duration: {{ duration }}s</div>

<div class="stats">
  <div class="stat blue"><div class="label">Total Found</div><div class="value">{{ total_found }}</div></div>
  <div class="stat green"><div class="label">Validated</div><div class="value">{{ total_validated }}</div></div>
  <div class="stat yellow"><div class="label">Services</div><div class="value">{{ services_count }}</div></div>
</div>

<table>
  <thead>
    <tr>
      <th>Service</th>
      <th>Key</th>
      <th>Repository</th>
      <th>File</th>
      <th>Status</th>
      <th>Info</th>
    </tr>
  </thead>
  <tbody>
    {% for f in findings %}
    <tr>
      <td><span class="badge service-badge">{{ f.service }}</span></td>
      <td><span class="key">{{ f.masked_key }}</span></td>
      <td><a href="{{ f.source_url }}" target="_blank">{{ f.repo }}</a></td>
      <td style="color:var(--muted); font-size:0.75rem;">{{ f.file_path }}</td>
      <td><span class="badge {% if f.validated %}valid{% else %}invalid{% endif %}">{% if f.validated %}VALID{% else %}unverified{% endif %}</span></td>
      <td class="credits">{% if f.credits is not none %}{{ f.credits }} credits{% endif %}</td>
    </tr>
    {% endfor %}
  </tbody>
</table>
</body>
</html>
"""

try:
    from jinja2 import Template
    _HAS_JINJA = True
except ImportError:
    _HAS_JINJA = False


def generate_html_report(result: ScanResult) -> str:
    findings_data = [
        {
            "service": f.service.value.upper(),
            "masked_key": f.masked_key,
            "source_url": f.source_url,
            "repo": f.repo,
            "file_path": f.file_path,
            "validated": f.validated,
            "credits": f.credits,
        }
        for f in result.findings
    ]

    if _HAS_JINJA:
        template = Template(HTML_TEMPLATE)
        return template.render(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
            duration=f"{result.scan_duration:.1f}",
            total_found=result.total_found,
            total_validated=result.total_validated,
            services_count=len(result.services_scanned),
            findings=findings_data,
        )

    # Fallback without jinja2
    rows = ""
    for f in findings_data:
        status = "VALID" if f["validated"] else "unverified"
        badge_cls = "valid" if f["validated"] else "invalid"
        credits_str = f"{f['credits']} credits" if f["credits"] is not None else ""
        rows += f"""<tr>
      <td><span class="badge service-badge">{f['service']}</span></td>
      <td><span class="key">{f['masked_key']}</span></td>
      <td><a href="{f['source_url']}" target="_blank">{f['repo']}</a></td>
      <td style="color:var(--muted); font-size:0.75rem;">{f['file_path']}</td>
      <td><span class="badge {badge_cls}">{status}</span></td>
      <td class="credits">{credits_str}</td>
    </tr>"""

    html = HTML_TEMPLATE
    html = html.replace("{{ timestamp }}", datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"))
    html = html.replace("{{ duration }}", f"{result.scan_duration:.1f}")
    html = html.replace("{{ total_found }}", str(result.total_found))
    html = html.replace("{{ total_validated }}", str(result.total_validated))
    html = html.replace("{{ services_count }}", str(len(result.services_scanned)))
    # Remove jinja2 loop and replace with rows
    import re
    html = re.sub(r'\{%.*?%\}', '', html, flags=re.DOTALL)
    html = html.replace("{{ f.service }}", "").replace("{{ f.masked_key }}", "").replace("{{ f.source_url }}", "").replace("{{ f.repo }}", "").replace("{{ f.file_path }}", "").replace("{{ f.validated }}", "").replace("{% if f.validated %}valid{% else %}invalid{% endif %}", "").replace("{% if f.validated %}VALID{% else %}unverified{% endif %}", "").replace("{% if f.credits is not none %}{{ f.credits }} credits{% endif %}", "")
    html = html.replace("<tbody>\n    \n  </tbody>", f"<tbody>{rows}</tbody>")
    return html
