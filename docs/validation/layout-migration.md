# Directory organisation verification

The team leader requested a simpler local folder and GitHub layout. Source modules remain under src/memory_lab and the desktop launcher remains at the project root. Local cache, model files, Chroma index, runtime ledger and bootstrap tools now live under ignored .local/. The Python interpreter and .venv retain their original locations.

Each run retains its original manifest.json at the root, with raw logs under raw/, input snapshots under inputs/ and existing derived tables/figures under analysis/. The [migration map](layout-migration.json) records all 40 live artifacts, their old/new paths and SHA-256 hashes. All original contents are unchanged. Offline artifacts were moved with the same hash checks but remain local-only.

Verification:

- 24 automated tests passed, including new/grouped paths, legacy/flat compatibility, duplicate-artifact rejection and preservation of an existing cost ledger.
- All 66 original experiment files (live and offline) matched their pre-migration SHA-256 hashes. Only the result-navigation README was edited.
- Both grouped and flat copies of the full 300-trial formal archive reproduced every existing summary metric exactly. Reanalysis was performed on local scratch copies, not the immutable archive.
- The relocated Chroma index still validates all 100 memory IDs, owners and contents.
- The existing cost ledger is unchanged (cumulative estimate USD 0.2017431); no paid API call was made for organisation.
- UI test journals now use temporary test directories instead of appending to project demo logs.
- Bootstrap uv and pip remained usable after moving their local tool environment.
- Markdown links and local-secret/runtime/IDE ignore rules passed checks.
- The retained desktop launcher runs headlessly without Streamlit onboarding prompts; the service health endpoint is ok and the moved formal table/three figures load in the UI.

Existing manifests still reference the historical experiment source and model paths; these records were not rewritten to pretend the experiment ran after the organisation. New experiments use the current layout and a new frozen manifest. The current reader also accepts older flat run directories.
