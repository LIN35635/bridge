# OKX Exchange-Side Stop Protection Audit

## Query every conditional order type first

- Treat "no stop on the exchange" as a claim that needs a complete query, not a default reading of an empty result.

- Query all conditional order types the venue supports before you conclude anything. On OKX that means conditional orders, OCO orders, trigger orders, and move_order_stop orders together.

- Remember that an OKX trade-page 止盈止损 order is ordType OCO. A query that only asks for conditional orders will miss it and produce a confident false negative.

- Use the read-only helper documented in the connector doc below instead of hand-rolling API queries, and read its stop-audit output before you report.

## Report what you found

- Name the stop you found with its trigger price, order type, side, and time placed.

- Compare the trigger distance against the position's own stop rule and show the arithmetic.

- Distinguish exchange-side protection from a mental stop or a chat promise. Only an order resting on the exchange counts.

- Say exactly which order types you checked when the complete query finds nothing, so the absence is verifiable.

## Present facts against the user's rules

- Report the numbers first, then flag deviations such as a missing stop or a stop placed farther than the rule allows.

- Never soften a partial query into a verified absence, and never present an unchecked order type as checked.

- When the user corrects you, concede the miss, name the order type you skipped, and fix the query the same day.

## Available connectors

- [OKX (custom.okx)](~/workspace/custom-connectors/custom.okx/CONNECTOR.md) for the local read-only helper that reads balances, positions, fills, and conditional orders.

- Use `muse.connector_search` to find other connectors and `muse.skill_search` to find related skills.

- If nothing here fits, look on the web for a maintained API or MCP server and set it up with [Custom Connectors and MCPs](/opt/muse/skills/custom-connector-setup/SKILL.md), or build a custom connector.

## Alternatives for better results

- Cross-check the venue's trade page when the API result is ambiguous, and treat the page as the tiebreaker only after the full order-type query.

- Ask the user for a screenshot of the open stop order when neither the query nor the page resolves it, instead of asserting that no stop exists.
