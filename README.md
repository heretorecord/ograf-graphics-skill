# ograf-graphics (Claude Agent Skill)

Create broadcast graphics that conform to the **EBU OGraf v1** specification, so they
run in any OGraf-compatible renderer. This repository is the **source of truth** for the
skill; the distributable `.skill` file is a build artifact you generate from it.

## Repository layout

```
ograf-graphics/
├── SKILL.md                  # the skill (instructions + triggering description)
├── references/               # detail docs loaded on demand
│   ├── manifest-spec.md
│   ├── component-interface.md
│   └── brand-kit.md
├── assets/
│   ├── schemas/              # bundled EBU JSON Schema set (MIT — see THIRD_PARTY.md)
│   └── templates/            # starting manifest, component, brand-kit
├── scripts/
│   ├── validate_ograf.py     # spec gate: manifest schema + interface + JS syntax
│   ├── check_brand.py        # advisory brand-consistency check
│   ├── package.sh            # build the .skill from this folder
│   └── requirements.txt      # python deps for the scripts
├── README.md
├── CHANGELOG.md
├── THIRD_PARTY.md
└── .gitignore
```

## Working on the skill

```bash
# one-time: deps for the validator
pip install -r scripts/requirements.txt

# validate a graphic you build with the skill
python3 scripts/validate_ograf.py path/to/<graphic-folder>

# build the distributable .skill (zip of this folder)
bash scripts/package.sh           # -> ograf-graphics.skill in the parent dir
```

The `.skill` is just a zip of this folder, so `package.sh` is a convenience — any zip of
the folder (with `SKILL.md` at its root) works. Install it wherever you load skills.

## Versioning

Bump the version in `CHANGELOG.md` (and tag the repo) when you change behaviour. The
skill's identity is its folder name + `SKILL.md`; keep them stable.

## Updating the bundled schemas

The EBU schema set under `assets/schemas/` is vendored from
`github.com/ebu/ograf` (`v1/specification/json-schemas/`). To refresh:

```bash
curl -sL https://codeload.github.com/ebu/ograf/tar.gz/refs/heads/main -o /tmp/ograf.tgz
tar xzf /tmp/ograf.tgz -C /tmp
rm -rf assets/schemas && cp -r /tmp/ograf-main/v1/specification/json-schemas assets/schemas
python3 scripts/validate_ograf.py assets/../assets/templates   # sanity-check it still validates
```

Note: the schema in the repo's `main` branch is newer than the one served at the live
`$schema` URL. See `references/manifest-spec.md` for the implications.

## License

This project is licensed under the MIT License — see `LICENSE`. Bundled EBU schemas are
also MIT — see `THIRD_PARTY.md`.
