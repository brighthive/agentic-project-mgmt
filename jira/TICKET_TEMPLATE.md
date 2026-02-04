# Jira Ticket Template

Use this template when creating new Jira tickets.

---

## Template

```
📝 Description

[Clear description of what needs to be done and why]

📍 Scope

**Include:**
- [What is in scope]
- [Features/changes to implement]

**Exclude:**
- [What is explicitly out of scope]
- [Future work not in this ticket]

🏗️ Areas

[Affected systems/components, e.g.:]
- BrightAgent
- Webapp
- Core
- Platform

✅ Acceptance Criteria

- [ ] [Criteria 1]
- [ ] [Criteria 2]
- [ ] [Criteria 3]

👥 Contact

**Stakeholders:** @[names]

🔧 Technical Notes

[Technical implementation details, architecture decisions, etc.]

💼 Business Notes

[Business context, user impact, priority reasoning]

📎 Attachments

[Links to designs, specs, screenshots]

🔗 Related Issues

- Related to #[issue number]
- Blocks #[issue number]
- Blocked by #[issue number]
```

---

## Example: BH-241 Projects BHAgent Integration

```
📝 Description

Brightagent: First version of Brightagent integration with projects will be the addition of deepagent's capabilities + the knowledge of the current project it is at in the context to provide replies to the user tailored to the scope of the PROJECT ONLY

Front-End: we would only display chat as a v1 and then we will discuss how to display all the outputs that is beings displayed in brightagent session in the brigthagent-omni sidebar chat as a v2

This would be added in Projects in a way to fit in the new design of the projects

📍 Scope

**Include:**
- Chatting to the agent within projects
- Using the attached resources
- Keep chat history that is within the project

**Exclude:**
- Hard restrictions on what the agent can access

🏗️ Areas

- BrightAgent
- Webapp
- Core

✅ Acceptance Criteria

- [ ] Able to chat to agent
- [ ] Agent can keep chat history
- [ ] Agent uses the attached resources

👥 Contact

**Stakeholders:** @Harbour @Marwan

🔧 Technical Notes

--

💼 Business Notes

-

📎 Attachments

-

🔗 Related Issues

- Parent: BH-116 (Projects EPIC)
```
