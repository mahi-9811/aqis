# Web App

React frontend for AQIS.

The supported backend path is the Java gateway. The UI should not call the Python API directly by default.

## Run

```bash
npm install
npm run dev
```

Default API behavior in development:

- Browser requests `/api/predictions/...`
- Vite proxies `/api` to `http://localhost:8080`

Optional override:

```bash
VITE_API_BASE_URL=http://localhost:8080/api/predictions
```

The UI supports:

- history lookup by test name
- artifact upload using `log.xml`, `STARTLog.txt`, and an optional screenshot
