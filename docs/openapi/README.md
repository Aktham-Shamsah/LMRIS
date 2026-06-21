# OpenAPI Export

Run the backend, then export the OpenAPI JSON:

```powershell
Invoke-WebRequest http://localhost:8000/openapi.json -OutFile D:\pyML\lrmis\docs\openapi\openapi.json
```

Swagger UI is available at:

```text
http://localhost:8000/docs
```

