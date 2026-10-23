# Discretionary Trading Method Fidelity

## Keep the stated method verbatim

- Record the user's method in their own words before you add anything.

- Add no indicator, filter, confirmation, or named pattern the user did not state.

- Treat an example or a chart explanation as an explanation, not as a new rule.

- Ask for explicit approval before you turn a discretionary method into code or a scored system.

- Stop adding structure after a correction and remove the added rule instead of defending it.

- Present the method back and wait for confirmation when the user corrects it twice.

## Use one risk definition

- Write each risk quantity once in one place with its unit and its base.

- Distinguish margin from nominal exposure and price move from account loss.

- Show the arithmetic from margin through leverage and stop to account loss in one place.

- Recompute from that single definition when a number changes and never restate a derived number from memory.

- Ask which definition the user means when margin and nominal could differ, and wait for the answer before you trade or test.

## Test a method honestly

- State the holding cap, costs, funding, liquidation, and benchmark before you report a result.

- Count a trade that would have exceeded the holding cap as exited at the cap, not as held to a later win.

- Compare the result with holding the underlying asset over the same period.

- Report trades, win rate, drawdown, and the largest win separately, and name any single trade that drives the total.

- Label a result as untested when costs, funding, or liquidation are missing, and do not present it as a live expectation.

- Refuse a guaranteed return target when no verified method supports it, and offer the honest comparison instead.

## Keep code and configuration in parity

- Read the configuration and the code that uses it before you report a signal or a test.

- Change a threshold in one place and verify that every consumer reads the same value.

- Reproduce a rejected signal with the same inputs the live code used, and name the threshold that rejected it.

- Keep a demo or fallback signal labeled as demo until live data replaces it, and do not present fallback output as market data.

- Retire a coded system the user discards, and do not keep tuning it or reintroduce its rules under a new name.

## Available connectors

- Use `muse.connector_search` to find other connectors and `muse.skill_search` to find related skills.

- If nothing here fits, look on the web for a maintained API or MCP server and set it up with [Custom Connectors and MCPs](/opt/muse/skills/custom-connector-setup/SKILL.md), or build a custom connector.

## Alternatives for better results

- Offer a trade diary that records the setup, the decision, and the outcome in the user's own words.

- Offer a checklist for one manual review instead of a coded system when the method stays discretionary.

- Offer a simple arithmetic check for one proposed trade before any broader test.
