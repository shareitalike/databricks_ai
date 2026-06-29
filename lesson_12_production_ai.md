# Lesson 12: Handling Breaking Changes in Production

You asked an incredibly important question: *If we lock our versions in production (using `requirements.txt`), but a mandatory upgrade is required (e.g., a critical security vulnerability patch or a required cloud update), how do we handle breaking changes like `state_modifier` vs `messages_modifier` without crashing the live production app?*

In enterprise AI engineering, we use a robust set of CI/CD (Continuous Integration / Continuous Deployment) practices to ensure that mandatory upgrades never impact live users.

## The Production Lifecycle

Here is exactly how a team handles a mandatory library upgrade:

### 1. The Alert
The team receives an alert that a library (like `langgraph`) must be upgraded from `0.1.x` to `0.2.x` due to a security vulnerability.

### 2. The Sandbox Branch
An AI Engineer creates a new branch (e.g., `feature/upgrade-langgraph-0.2`) from the main code.
They open a development environment (like the Databricks notebook you are using now) and run `%pip install -U langgraph`.

### 3. Automated Testing (CI)
The engineer runs the automated test suite. The tests immediately fail with the error:
`TypeError: create_react_agent() got unexpected keyword arguments: {'state_modifier'}`

> [!TIP]
> **Why tests are critical:** In production, you don't discover these errors by manually clicking buttons in the UI. You write Python `pytest` scripts that automatically run your Omni-Agent with 50 different questions every time the code changes. If a single test fails, the code is physically blocked from being deployed to production.

### 4. Code Remediation
The engineer sees the test failure, reads the LangGraph migration documentation, and realizes they need to change the argument from `messages_modifier` to `state_modifier`.
They update `omni_agent.py`, push the code, and the automated tests run again. This time, they pass!

### 5. Blue/Green Deployment
Even though the tests passed, the team doesn't just overwrite the live production model. They use **Blue/Green Deployment**:
* **Blue (Old):** The live production app currently serving users (running `langgraph 0.1.x`).
* **Green (New):** A completely new, isolated server/cluster is spun up running the new code (with `langgraph 0.2.x` and the `state_modifier` fix).

The team routes a tiny amount of traffic (e.g., 5% of internal employee requests) to the **Green** environment to ensure it works perfectly in the real world. 

### 6. The Switch
Once the Green environment is verified, the network router is updated to send 100% of traffic to the Green environment. The old Blue environment is safely deleted. 

> [!IMPORTANT]
> **Zero Downtime:** Because of this strategy, the live user never experiences a crash, an import error, or any downtime. The breaking change was caught by tests, fixed in isolation, and smoothly swapped in!

---

### In Summary
You never upgrade packages directly in the production environment. You lock them. When you *must* upgrade, you do it in an isolated branch, let the automated tests catch the breaking API changes, fix the code, and then deploy a brand new image alongside the old one before making the swap!
