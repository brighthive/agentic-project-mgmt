# JIRA Dashboard Setup - Best Gadgets

Based on research, here are the best gadgets for your metrics.

## Essential Gadgets for Your Metrics

### 1. Sprint Completion Rate
**Gadget:** Sprint Health Gadget (Native)
- Shows sprint progress, completion percentage, scope changes
- Highlights at-risk issues and blockers
- Best for: Daily standups and sprint retrospectives

### 2. Average Time Per Ticket
**Gadget:** Average Age Chart (Native)
- Filter: `project = BH AND status = Done AND resolved >= -30d`
- Shows average time from creation to completion
- Best for: Overall team efficiency

**Alternative:** Resolution Time Report
- More detailed breakdown by issue type
- Shows aging issues and bottlenecks

### 3. Sprint Velocity / Completion Rate
**Gadget:** Velocity Chart (Native)
- Shows story points committed vs completed per sprint
- Calculates average velocity over last 5-10 sprints
- Best for: Sprint planning and capacity forecasting

### 4. Customer Ticket Resolution Time
**Gadget:** Average Age Chart (Native)
- Filter: `project = BH AND (issuetype = Bug OR labels = "customer") AND status = Done`
- Tracks support/bug resolution performance

### 5. Major Feature Deployment (Epics)
**Gadget:** Average Age Chart (Native)
- Filter: `project = BH AND issuetype = Epic AND status = Done`
- Shows time from epic creation to completion

### 6. Roadmap Alignment
**Gadget:** Two-Dimensional Filter Statistics (Native)
- Row: Status
- Column: `labels = "roadmap"`
- Shows planned vs actual completion

**Alternative:** Roadmap Gadget
- Visual Gantt-style timeline
- Better for high-level progress tracking

## Bonus Recommended Gadgets

### 7. Sprint Burndown Chart
- Track daily progress toward sprint goal
- Essential for identifying velocity issues early

### 8. Created vs Resolved Chart
- Shows issue creation rate vs resolution rate
- Helps identify if backlog is growing or shrinking

### 9. Filter Results (Multiple)
- Create filtered views by assignee
- Quick snapshot of individual workloads

## Setup Steps

1. Go to: https://brighthiveio.atlassian.net/jira/dashboards
2. Click **Create dashboard**
3. Name: `BH Metrics Dashboard`
4. Click **Add gadget** and add each gadget above
5. Configure filters as shown

## Third-Party Options (Optional)

For advanced metrics, consider:
- **Great Gadgets for Jira** - Enhanced charts and KPIs
- **Agile Velocity & Sprint Status Gadgets** - Cross-team comparisons
- **Time Metrics Tracker** - Advanced resolution time tracking

These are marketplace apps that extend native functionality.

---

**Sources:**
- [Best Jira Dashboard Examples for 2026](https://hevodata.com/learn/jira-dashboard-examples/)
- [Top 10 Scrum Gadgets for Agile Dashboards](https://appfire.com/resources/blog/top-scrum-gadgets-for-agile-jira-dashboards)
- [9 Gadgets for Powerful Scrum Dashboard](https://community.atlassian.com/forums/App-Central-articles/9-gadgets-for-a-powerful-Scrum-dashboard-in-Jira/ba-p/1683063)
- [Resolution Time Gadget in Jira](https://community.atlassian.com/forums/App-Central-articles/Resolution-Time-Gadget-in-Jira-Ways-to-Calculate-Time-to/ba-p/2912004)
- [Jira Velocity Chart Guide](https://support.atlassian.com/jira-software-cloud/docs/view-and-understand-the-velocity-chart/)
- [12 Jira Performance Metrics Worth Tracking](https://jellyfish.co/library/jira-performance-metrics/)
