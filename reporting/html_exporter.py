"""Export scan results as HTML using Jinja2."""

import os
import jinja2
from datetime import datetime

def export_html(results, target, start_port, end_port, os_guess, filepath):
    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir))
    template = env.get_template("report_template.html")

    html = template.render(
        target=target,
        date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        start_port=start_port,
        end_port=end_port,
        os_guess=os_guess,
        results=results
    )
    with open(filepath, 'w') as f:
        f.write(html)
