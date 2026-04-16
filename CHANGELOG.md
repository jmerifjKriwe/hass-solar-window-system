# Changelog

## [2.1.3](https://github.com/jmerifjKriwe/hass-solar-window-system/compare/v2.1.2...v2.1.3) (2026-04-12)


### Bug Fixes

* **coordinator:** work around ruff format bug with exception syntax ([2e9f394](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/2e9f3943f929b31630ea859d055d8685b60b25d3))
* resolve type checking issues and update imports ([8522b61](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/8522b61564cd23ac8f2a0aa483e0c47ae3c1de22))
* **tests:** correct DeviceInfo import path for pyright compliance ([91bc464](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/91bc4641dc20f51f84bb6da32c0d70260d2fa12b))

## [2.1.2](https://github.com/jmerifjKriwe/hass-solar-window-system/compare/v2.1.1...v2.1.2) (2026-04-11)


### Bug Fixes

* correct exception syntax and update hacs.json filename ([a1b6a1c](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/a1b6a1c5de4e78ad4878816c8fbf104a79bf8e16))

## [2.1.1](https://github.com/jmerifjKriwe/hass-solar-window-system/compare/v2.1.0...v2.1.1) (2026-04-11)


### Bug Fixes

* **release:** correct release-please config and HACS ZIP structure ([bef1343](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/bef1343b0481fc9ca84e62c5d59a44cbf38e48ee))

## [2.1.0](https://github.com/jmerifjKriwe/hass-solar-window-system/compare/v2.0.1...v2.1.0) (2026-03-04)


### Features

* add commit message validation and improve release automation ([a53cb9c](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/a53cb9cafb689c6c7f228ff813cccd836e16ee1b))
* add coordinator structure ([8948c63](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/8948c631611ba2de4facaea2ab858bb4683877ee))
* add core constants and domain setup ([73826f3](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/73826f3cf10f8c150d097950faded5370a6c17cd))
* add project foundation and CI/CD ([4a3c1a8](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/4a3c1a8a0d01dcbf8b2ea8e6c1699b917094cd1d))
* add quality gate, pre-commit hooks, and dev environment setup ([6027c1d](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/6027c1d8ef47e8cd2bf25b9070b8b4011746d3a2))
* add Windows support and update tooling ([6dc0853](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/6dc085322444608d6947a2b4fa711d05e2624eaf))
* implement configuration storage ([1618703](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/1618703ba7d069412dceced3c82a4cbd7e7bb945))
* implement diffuse radiation estimation ([dd52355](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/dd52355c842261b141e0a48064a0984c12ec0d71))
* implement energy sensor entities ([4904258](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/49042580042619019b3b9a2fdf2cc1ccbee1c417))
* implement group and global aggregation ([5a6425d](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/5a6425dc75713d0f0dc1156273858fd2a4431dfa))
* implement main solar calculation update loop ([920a537](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/920a53790936c333f00c2ca14fe22bb7bcf45864))
* implement safe sensor reading ([df13191](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/df1319113efead3ab91294becb3bfb4f036cf15e))
* implement sun visibility calculation ([f7bc7c1](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/f7bc7c1d09f1437b51d2fb12aca3e67e38bcc25f))


### Bug Fixes

* add config flow and fix manifest validation errors ([61fb8b1](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/61fb8b1ef58782b6238e9abed8ca30e653d9c1ca))
* add issue_tracker to manifest.json ([c8e518f](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/c8e518fc021b932d82ce28cb1a407bf4499220e2))
* **config_flow:** resolve pyright errors by removing domain parameter and adding DOMAIN class variable ([2863fee](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/2863fee8bb4a303651bf71e7431a16547bd99e2f))
* correct atan2 parameter order in shade angle calculation ([5abfd73](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/5abfd734d18144caf3eddc82b8ba0226e17e7ac4))
* **hooks:** handle multi-line commit messages correctly ([06477bf](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/06477bfed272a6b5015e333612a06a1a1a02cf61))
* resolve type safety issues in coordinator update loop ([f083063](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/f083063e1caa293c1e43313a02467349515c443c))


### Documentation

* Add comprehensive design document for Solar Window System ([fdc3958](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/fdc395851ec9261945bf3041cd9e75d2c8c09b20))
* add comprehensive documentation ([94081cb](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/94081cbf97f207b6798045a32ce6934400824fb5))
* add comprehensive implementation plan ([8d16037](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/8d160371b2ca1eea626e1c69984438a662adadde))
