# Site Data Update Verification

## Sync before you edit

- Pull the latest remote version before you touch any file, since other editors can change the same site without telling you.

- Read the pulled files and confirm the current data is intact before you plan the change.

- Record the remote commit or version you started from so you can roll back to it.

## Change safely and preview locally

- Back up the file you are about to edit, then make the change.

- Re-read the edited file and confirm every confirmed number, label and status is still present and unchanged except for the intended edit.

- Open the edited page in a local browser preview and click through the changed area, the surrounding modules and the stored data path.

- When the site uses browser storage, bump the storage key version on schema changes so old cached data cannot mask the new deploy.

## Publish and wait for the live build

- Push the change through the channel that works here, such as the connector API or the browser, and capture the commit or push result.

- Wait for the hosting platform's build to finish before you check anything, since the live URL lags the repository by minutes.

- Never announce completion from a local preview or a successful push alone.

## Verify the live site before you announce

- Load the live URL in a fresh session with caches cleared and confirm the new data renders on screen.

- Compare the live page against the intended change, including data the user reported missing before.

- Only after the live check passes, tell the user the update is done and name what you verified.

- If the live page still shows old data, diagnose cache, build lag or an incomplete edit yourself instead of asking the user to test.

## Available connectors

- [GitHub](/opt/hatch/connectors/github/CONNECTOR.md) for reading and changing repository files, commits and pull requests.

- [custom.github](~/workspace/custom-connectors/custom.github/CONNECTOR.md) for the registered GitHub API route when it is reachable from this environment.

- Use `muse.connector_search` to find other connectors and `muse.skill_search` to find related skills.

- If nothing here fits, look on the web for a maintained API or MCP server and set it up with [Custom Connectors and MCPs](/opt/muse/skills/custom-connector-setup/SKILL.md), or build a custom connector.

## Websites

- [GitHub](https://github.com/) for pushing changes when the API is unreachable from this environment. Carry the repository name, branch and exact file path into `browser.browse`, and verify the commit appears in the repository history.

- The site's own live URL for the final check. Carry the exact page and the expected data into `browser.browse`, and verify the data renders in a fresh load.

## Alternatives for better results

- When the platform offers deploy previews, check the preview link before merging so the live check rarely surprises you.

- Ask the user to hard refresh only as a diagnostic after you have confirmed the deploy is live, never as the fix itself.

- Keep a short log of commit, build time and live check result so a repeat report is easy to trace.
