# Frontend files

The repository contains two different frontend experiences and a separate
static packaging script:

- `phirFinal.optimized.html` is the source used by the current fast-package
  builder. It is the stylized presentation/role experience.
- `phirFinal.html` is the older standalone version and is retained as a source
  artifact; it is not the input to the fast-package builder.
- `../demo/index.html` is the small functional client served by
  `../scripts/run_demo.sh` for local API development.

## Build the stylized frontend package

From the repository root:

```bash
python3 scripts/build_fast_frontend.py
```

The script extracts/static-packages its source into `dist/phir-fast/`. That
directory is generated and ignored by Git. Keep it as a build artifact; edit
the source and the checked-in supporting scripts/media instead.

The page uses the bridge scripts in this directory to call the HTTP API.
`phir-config.js` currently sets the deployed API Gateway URL. The package is
therefore not automatically connected to `localhost:8080`, and the local demo
server serves `demo/`, not this frontend. For local integration, set
`window.PHIR_API_BASE` to the local API origin before the bridge scripts load
and serve the package over HTTP; verify endpoint compatibility before relying
on the full flow.

`backend-context/` contains archived backend snapshots for context only.
