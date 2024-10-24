# Changelog

This file includes a history of past releases. Changes that were not yet added to a release are in the [changelog.d/](./changelog.d) folder.

<!--
⚠️ DO NOT ADD YOUR CHANGES TO THIS FILE! (unless you want to modify existing changelog entries in this file)
Changelog entries are managed by scriv. After you have made some changes to this plugin, create a changelog entry with:

    scriv create

Edit and commit the newly-created file in changelog.d.

If you need to create a new release, create a separate commit just for that. It is important to respect these
instructions, because git commits are used to generate release notes:
  - Modify the version number in `__about__.py`.
  - Collect changelog entries with `scriv collect`
  - The title of the commit should be the same as the new version: "vX.Y.Z".
-->

<!-- scriv-insert-here -->

<a id='changelog-19.0.0'></a>
## v19.0.0 (2024-10-24)

- [Bugfix] Fix legacy warnings during Docker build. (by @regisb)

- 💥[Feature] Update Xqueue Image to use Ubuntu 24.04 as base OS. (by @jfavellar90)

- 💥[Feature] Upgrade to Sumac. (by @jfavellar90)

<a id='changelog-18.0.0'></a>
## v18.0.0 (2024-05-09)

- [Bugfix] Make plugin compatible with Python 3.12 by removing dependency on `pkg_resources`. (by @regisb)

- 💥[Feature] Upgrade Python version to 3.12.3. (by @jfavellar90)
- 💥[Feature] Upgrade to Redwood. (by @jfavellar90)

<a id='changelog-17.0.0'></a>
## v17.0.0 (2023-12-09)

- 💥 [Feature] Upgrade to Quince (by @jfavellar90).
- [Improvement] Add a scriv-compliant changelog. (by @regisb)
- [Improvement] Removing the xqueue permissions container in favor of a global single permissions container. (by @jfavellar90)
- [Bugfix] Fix "Error: service "xqueue-job" depends on undefined service mysql: invalid compose project" - add conditional statement to check whether the mysql service is enabled or if the user is using an external mysql instance. (by @ravikhetani)
- [Improvement] Added Typing to code, Makefile and test action to the repository and formatted code with Black and isort. (by @CodeWithEmad)


