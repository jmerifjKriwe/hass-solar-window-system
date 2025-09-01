# CHANGELOG

<!-- version list -->

## v2.0.0 (2025-09-01)

### Bug Fixes

- Resolve blocking I/O and visibility calculation issues
  ([`c8ff043`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/c8ff0434d70713f15cedcfafb2888ec0c32aca4f))

- Resolve empty current_sensor_states in debug output
  ([`9a05c3f`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/9a05c3f1ecad8fcce1f8297b025f514e7729b2d2))

- Update documentation and improve sensor platform
  ([`abdea44`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/abdea4425e8a4a2f46b19730c8a91b5cc95ed3e8))

- **services**: Resolve device IDs to subentry IDs in debug calculation service
  ([`dc1843e`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/dc1843e3bb1a092671be64e2d1fcece8cbb4ab53))

- **tests**: Resolve failing tests and improve test isolation
  ([`ca924ae`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/ca924ae5f4f6e71a78175aaab729e07663a347f7))

### Build System

- **deps**: Bump ruff from 0.12.10 to 0.12.11
  ([`0e62379`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/0e6237971072bc10530dde859ebf10f676fa674b))

### Chores

- Delete logo
  ([`e382f1d`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/e382f1d253c68a87b76f259457658004e8adb141))

- **ci**: Prevent release failure on concurrent pushes by checking ancestry
  ([`5a9290b`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/5a9290b2ad894332f6007f10683e17f0cb809a64))

- **ci**: Update workflow permissions and clarify commit guidelines
  ([`22fff66`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/22fff66b61fe7b6538cc543f35e6a4e325277ec1))

- **refactor**: Complete modular architecture refactoring
  ([`623b0e6`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/623b0e691cba01b30b42d7f2cf6d1d954d066cc1))

### Documentation

- Update coverage badge
  ([`40a2d61`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/40a2d61adcc3f3f0a719326a62c0e81b71e94df0))

### Features

- Enhance solar calculation system and add version display
  ([`c35b747`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/c35b747432611b1ce0eb47ad136ad743320837b3))

- **calculator**: Add async batch processing and type fixes
  ([`e31f17d`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/e31f17d0f93276dbaaceacdbfa3a9633fb545eca))

### Refactoring

- Complete Ruff linting compliance and code quality improvements
  ([`93471d5`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/93471d524103991cbebd09d6e9b23e87d851e1fc))

- Consolidate shared utilities and remove obsolete helpers.py
  ([`7955a5c`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/7955a5c073058bfb803eaa136809d76b060051ac))

- **architecture**: Implement modular mixin architecture
  ([`4d2a3af`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/4d2a3af260c29b9161e05732f5ed262a4046a737))

- **calculator**: Modularize solar calculation system
  ([`3fed8d3`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/3fed8d3d0034459aec193d1eeba3e65dcf644a85))

- **platforms**: Extract common base class for global config entities
  ([`3b99653`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/3b9965376c3346e85ea6e1b3d93bb068bf9a583b))

### Testing

- Fix ERROR logs in pytest output by adding caplog to exception tests
  ([`257ee1b`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/257ee1b5134e863c30ba5d55e9aa8f849e71c863))


## v1.2.0 (2025-08-29)

### Documentation

- Update coverage badge
  ([`879e44e`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/879e44e5435964331222820ce3ac72e723367807))

### Features

- Add debug calculation service and comprehensive tests
  ([`582b923`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/582b923a02f6c5d34d4258b61f45a47f34fd74fc))


## v1.1.1 (2025-08-28)

### Bug Fixes

- **ci**: Correct YAML syntax in lint workflow
  ([`ef39947`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/ef3994733500c04e60767794cc6355dacc4ae632))

- **test**: Resolve diagnostics snapshot test failure
  ([`22c715c`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/22c715ce9ca4effe544950c8cc17a904d747757f))

### Build System

- **deps**: Bump actions/checkout from 4 to 5
  ([`285c472`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/285c472ca061032fc9e756dec634ed3af1c19257))

- **deps**: Bump stefanzweifel/git-auto-commit-action from 5 to 6
  ([`f4692c9`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/f4692c927405b9eb5a8c8e46c86b349c9db78d24))

### Chores

- Clean up debug steps and temporary files
  ([`30f56d2`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/30f56d26350f53b2c4622a6dce09bdfde101a265))

- Fix linting errors and improve code quality
  ([`a417b77`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/a417b77966eba5dce4d6bde383d652f1fec70e7b))

- Remove preview mode to match CI behavior
  ([`2126399`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/21263998695669a02fb9877edaec5292a374cc1f))

- Resolve all ruff linting errors
  ([`baa54b0`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/baa54b0baaccb9dfbd849ed2f7a903b8e82b0dcc))

- Resolve I001 import sorting errors
  ([`4390933`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/439093398cad1b0d44b93a43062d1089ef1a29cd))

- **ci**: Add ruff debug steps to lint workflow for settings comparison
  ([`fdaa3fc`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/fdaa3fc4be851116ebfed76a5b25c2ad3ff63e53))

- **ci**: Add ruff debug steps to lint workflow for settings comparison
  ([`38b83bf`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/38b83bf49dc7a7f65dc79e7979b7d509a65496c8))

- **ci**: Ensure ruff uses local config in CI
  ([`ac81473`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/ac81473cf01249d1a88708a00d39d6020cb33c7b))

- **lint**: Fix import sorting and type annotation issues
  ([`c6ec626`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/c6ec6260ba582ecaa6d6b42ac18c9bd2d988381b))

### Testing

- **diagnostics**: Remove unused snapshot and update snapshots
  ([`9136ed5`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/9136ed582ec2891f81234a882d7e7abb0f61802a))


## v1.1.0 (2025-08-28)

### Bug Fixes

- **tests**: Address linting issues and improve test quality
  ([`66df3d2`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/66df3d22cb3f06f784c9e0e40457893698ae9130))

- **tests**: Reduce noisy test lints (add test ruff exemptions and pyproject updates)
  ([`336f9c6`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/336f9c6acde493e4004556cdb1ba81995e73d539))

- **tests**: Repair helpers and make ruff-clean for snapshot PoC
  ([`4628e31`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/4628e31de63beb502fcba0f14321692a4b56e70d))

- **tests**: Silence deliberate asserts and reduce noisy lints (S101, per-file test exceptions)
  ([`1a1fbdc`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/1a1fbdc75214ee5067005fcfdcfb9ac19974abce))

- **tests**: Stabilize and clean test_calculator_flow_based.py for deterministic snapshots
  ([`3f8734e`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/3f8734e704145d375f9ef95fc8f38250c6c5c2f1))

- **tests**: Tidy test_calculator_flow_based.py (apply ruff fixes, reduce noisy findings)
  ([`c05fe35`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/c05fe35bb5be3254252a59a40f812b4a0ebe171f))

### Build System

- **deps**: Bump actions/checkout from 4 to 5
  ([`71623a7`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/71623a7aab8212bcd6fc9a4745b830991375d092))

- **deps**: Bump home-assistant/actions
  ([`3c3a499`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/3c3a499f609df9abb764b93e9873b6d514b6260d))

- **deps**: Bump ruff from 0.12.5 to 0.12.10
  ([`bbf7a98`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/bbf7a984f4c6a39d3868e83a703dfb4562999c4c))

### Chores

- Commit remaining workspace changes
  ([`1de2c36`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/1de2c36a1936ba820197cdc78e1d422d43b9f82a))

- Deleted "Upload | Distribution Artifacts" from release.yml
  ([`a987d9e`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/a987d9ec0cc9f6e36070e359b73687b81f058699))

- Small adjustments for github actions
  ([`5801546`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/5801546e89dac60d188ab5571826e8e4a7487a5b))

- Update of readme.md
  ([`a26896e`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/a26896e6b0d3a0576eb9eb770270f990d706e020))

- **tests**: Add config_flow happy-path and duplicate-name tests
  ([`9a76ff9`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/9a76ff9590bf62905d4e43d8b93ce7c28aa791d6))

- **tests**: Add fixtures helper and parametrized platform PoC; move legacy platform tests to
  tests/old
  ([`4279126`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/4279126e7e647c02c0afae34d21201a31721fdf5))

- **tests**: Add initial diagnostics snapshots
  ([`1aa08ce`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/1aa08ce978ae4cfaf45d38c378eac94b0c2a4388))

- **tests**: Add tests/constants and helper collect_entities_for_setup_with_assert; use constants
  for global device
  ([`47654ea`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/47654eadc4d33e13310393b88a7ee6fc2838d90a))

- **tests**: Centralize fixtures usage in conftest and add tests/TODO.md
  ([`3e87ce7`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/3e87ce7952e005db8d85321a545b6ffc5b2fabcd))

- **tests**: Centralize unit fixtures and update coordinator tests
  ([`771edc0`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/771edc0da20ac66ec59b4cce4a1ccdc7a9a205a4))

- **tests**: Complete migration — include remaining modified tests
  ([`9a90a49`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/9a90a499b2e0732606ecd9c7b536e809916d9bdb))

- **tests**: Consolidate coordinator tests and remove duplicates
  ([`c1c7baf`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/c1c7bafda8ca4b0fef4d40204b6f4345adbd1561))

- **tests**: Fix pyproject.toml and tidy tests to restore pytest collection
  ([`33cc151`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/33cc151fc049e40ecda049c8ce10b16f405387a6))

- **tests**: Move entity tests to tests/old (batch 3)
  ([`59c30e2`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/59c30e24a0beb2db65b8de262b79cc5da1ca4232))

- **tests**: Move legacy platform tests to tests/old (batch 2)
  ([`acf331f`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/acf331f4baedc4184d186ada0536a307fb1aeeb6))

- **tests**: Move remaining legacy tests to tests/old (bulk)
  ([`50727c1`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/50727c139301ce7a9bc8fa757aa326fab4acc3dd))

- **tests**: Remove legacy platform test files (consolidated)
  ([`a1e7fb4`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/a1e7fb429f1ef70858611f5b5d2eca7601b5acb7))

- **tests**: Remove legacy tests/old archive
  ([`faaa135`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/faaa1350feef4aca9c5d2827db61dc8734f75dd8))

- **tests**: Reorganize and fix test documentation
  ([`eaaa966`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/eaaa9661f03735713f3536ef32dbaddb61c25004))

- **tests**: Use centralized unit fixtures in coordinator tests
  ([`925d0df`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/925d0dfc65071ee02fe264343a98466aee42bcd1))

- **tests**: Wip checkpoint — pause for today
  ([`fd56eb4`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/fd56eb427ba2c77dee59b63d6c3fdecb7868caf2))

### Code Style

- **tests**: Apply ruff --fix to tests
  ([`ad81f84`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/ad81f84fb0879f09ae1547d1e9c40c6c5a117372))

- **tests**: Fix config_flow PoC formatting and docstring
  ([`5298fd7`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/5298fd7795c7178adb43541ce306de3e1359ed35))

- **tests**: Lint and typing fixes for config_flow PoC tests
  ([`1b2e0bf`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/1b2e0bf50f9529d4c06f25e8333c564a1dd7c30e))

- **tests**: Ruff fixes for snapshot helpers and integration PoC
  ([`af1ecbc`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/af1ecbc6d425a5b604fcf6db467b27c47610cdbd))

- **tests**: Tidy conftest docstrings and linter fixes
  ([`ddcac4e`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/ddcac4e43c3a171254a0b12e5e4eaf2acf19bc9e))

### Documentation

- Update coverage badge
  ([`df52c24`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/df52c242156dfc291cf6aed663cf07ad93db1c57))

- **tests**: Document syrupy snapshot usage and CI guidance
  ([`9f61e6c`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/9f61e6c134aa77c0e3473bd228d507905e0bd27e))

- **tests**: Rename TESTING.md to README.md and add snapshot guidance
  ([`820c31a`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/820c31a832f18df6f67af957ac69276649766fb7))

### Features

- **tests**: Add number snapshot PoC
  ([`db75aae`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/db75aaef132b76f7e2d89223928db01d7594bf9a))

- **tests**: Add snapshot PoC tests and serializer helper
  ([`512b847`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/512b8477af3ef5977a7f2cf69ab4c10376cf75a8))

### Refactoring

- **test**: Migrate and reorganize test suite
  ([`eb0bfc6`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/eb0bfc6391e49594189cbab0f0ca58adc0cd086e))

- **tests**: Centralize fixtures and make global-config entry idempotent; update platform tests
  ([`c44c576`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/c44c5762e2cb86cd491b41bf1d4d3fd0ad8f3172))

- **tests**: Reorganize test structure and improve documentation
  ([`66f1bff`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/66f1bff2e0ac510d77db9e2020703db51a7b3f98))

- **tests**: Unify fixture names (provide canonical fixtures in helpers)
  ([`a1a1807`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/a1a1807b473a810cd7f720d1ff460cdd7d2adf12))

### Testing

- **config**: Add config_flow PoC import test
  ([`77bfed0`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/77bfed00a0a728bc9eb249df4c57ba09dc8c4acc))

- **config**: Add config_flow PoC tests for global and subentries
  ([`d5d1ce3`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/d5d1ce3749c654f4da84c126406e78238bb0eca0))

- **platforms**: Parametrize platform tests and skip legacy duplicates; mark TODO items 1-4 done
  ([`e8aa726`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/e8aa726b8fb51af58e2257006adaa91978c22621))

- **snapshot**: Normalize entity_id in number entity snapshot
  ([`af44ed1`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/af44ed1c67725521783657aaa9075ae97aedd15b))


## v1.0.0 (2025-08-22)

### Chores

- Another fix für release.yaml
  ([`9698ac5`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/9698ac5c7c02330edd842d39a19954efd7a46940))

- Debugging semantic_release
  ([`965d469`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/965d469d20d910afbb822221647d41b84d3e6895))

- Updated release.yml
  ([`9ba497f`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/9ba497f9ab599c9a9706665553258de6f720b297))

- **license**: Relicense project from MIT to MPL 2.0
  ([`0c4c19f`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/0c4c19ff89202b25831039c5bacbe92ac6cf6183))

### Features

- Another initial release
  ([`948f6f2`](https://github.com/jmerifjKriwe/hass-solar-window-system/commit/948f6f236722837f88b0daaa78310d3c7c2629af))


## v0.1.0 (2025-08-22)

- Initial Release
