# Frontend files

The repository contains two different frontend experiences and a separate
static packaging script:

- `phirFinal.optimized.html` is the source used by the current fast-package
  builder. It is the stylized presentation/role experience.
- `phirFinal.html` is the older standalone version and is retained as a source
  artifact; it is not the input to the fast-package builder.
- `../demo/index.html` is the small functional client served by
  `../scripts/run_demo.sh` for local API development.

## Rebuild the deployed frontend package

From the repository root:

```bash
python3 scripts/build_fast_frontend.py --output frontend/amplify-site
git diff --exit-code -- frontend/amplify-site
```

`amplify-site/` is the complete static package currently served by Amplify. It
is checked in so a clone contains the exact deployable HTML, all 44 media
assets, runtime scripts, map, and Amplify custom headers. The build command
regenerates that package from the source and supporting files in this
directory; `git diff --exit-code` confirms the generated copy matches the
checked-in artifact.

To preview the package from a clone, run:

```bash
python3 -m http.server 8090 --directory frontend/amplify-site
```

Then open <http://localhost:8090>. The page uses the checked-in API base URL
and therefore still needs a reachable backend for data-dependent flows.

The page uses the bridge scripts in this directory to call the HTTP API.
`phir-config.js` currently sets the deployed API Gateway URL. The package is
therefore not automatically connected to `localhost:8080`, and the local demo
server serves `demo/`, not this frontend. For local integration, set
`window.PHIR_API_BASE` to the local API origin before the bridge scripts load
and serve the package over HTTP; verify endpoint compatibility before relying
on the full flow.

`backend-context/` contains archived backend snapshots for context only.
