**Finance & Poverty Nexus – Rwanda**
**Financial inclusion intelligence for poverty reduction in Rwanda.**

This dashboard is a multi-page analytical web application designed for policymakers, NGOs, and field workers. It tracks financial inclusion metrics—specifically Digital Finance, Bank Loans, and Saving Groups (Ibimina)—and analyzes their impact on poverty reduction across Rwanda's 30 districts.

 **Core Features**
 * National Dashboard: High-level Key Performance Indicators (KPIs) and statistical correlations between financial access and poverty rates.

* Interactive Mapping : Geographic visualization of financial service reach using geoBoundaries spatial data.

* District Profiler & Comparison: Deep-dive analytics comparing individual district performance against national averages.

* Policy Simulator: An interactive forecasting tool allowing policymakers to adjust inclusion levers (e.g., increasing bank access by 10%) to project potential poverty reduction.

* Household Risk Calculator: A practical field tool that evaluates a household's vulnerability to poverty shocks based on their specific income source and financial footprint.

* Smart Action Plan: An automated, rule-based engine that generates customized, printable policy interventions for any selected district.

* Community Feedback (Live DB): A built-in reporting portal for field agents to log localized financial exclusion issues (e.g., "No Mobile Money Agent Nearby"), stored securely in a SQLite database.

**Technology Stack**

Backend: Python, Flask

Data Processing: Pandas, NumPy

Visualization: Plotly (plotly.express, plotly.graph_objects)

Database: SQLite (sqlite3)

Frontend: HTML5, CSS3, JavaScript (Jinja2 Templating)

Dataset: Built using microdata encompassing Rwanda's 30 districts (FinScope / EICV7).

