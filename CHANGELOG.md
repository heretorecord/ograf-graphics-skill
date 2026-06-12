# Changelog

## 1.1.0
- Intake now elicits editable fields explicitly, with a field-type → GDD mapping table.
- Added brand kits: `assets/templates/brand-kit.json`, `references/brand-kit.md`,
  `v_brand` provenance stamping, and `scripts/check_brand.py` (advisory).
- Component must self-default at load() so it never renders blank without injected data.

## 1.0.0
- Initial skill: OGraf v1 graphic creation with bundled schema set, dependency-free
  templates, and `scripts/validate_ograf.py` (manifest schema + interface + JS syntax).
