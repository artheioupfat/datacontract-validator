import os
import tempfile
import shutil
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datacontract.data_contract import DataContract

app = FastAPI(title="DataContract Validator API", version="1.0.0")

# CORS — allow GitHub Pages and local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Restrict to your GitHub Pages URL in production
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "ok", "service": "datacontract-validator"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/validate")
async def validate(
    parquet_file: UploadFile = File(...),
    yaml_file: UploadFile = File(...),
):
    """
    Validate a Parquet file against a datacontract.yaml.
    Returns the full datacontract-cli test report as JSON.
    """
    # Basic extension checks
    if not parquet_file.filename.endswith(".parquet"):
        raise HTTPException(status_code=400, detail="Le fichier de données doit être un .parquet")
    if not yaml_file.filename.endswith((".yaml", ".yml")):
        raise HTTPException(status_code=400, detail="Le contrat doit être un fichier .yaml / .yml")

    # Work in a temp directory that is cleaned up automatically
    tmp_dir = tempfile.mkdtemp(prefix="dcv_")
    try:
        parquet_path = Path(tmp_dir) / "data.parquet"
        yaml_path    = Path(tmp_dir) / "datacontract.yaml"

        # Save uploaded files
        with parquet_path.open("wb") as f:
            shutil.copyfileobj(parquet_file.file, f)
        with yaml_path.open("wb") as f:
            shutil.copyfileobj(yaml_file.file, f)

        # Patch the datacontract.yaml to point servers.local.path at our parquet
        _patch_yaml_server(yaml_path, str(parquet_path))

        # Run datacontract-cli validation
        dc = DataContract(data_contract_file=str(yaml_path))
        run = dc.test()

        # Serialize result
        result_dict = _serialize_run(run)
        return result_dict

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erreur de validation : {str(exc)}")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _patch_yaml_server(yaml_path: Path, parquet_absolute_path: str) -> None:
    """
    Inject a local server entry pointing to the uploaded parquet file
    so datacontract-cli can find the data even if the YAML doesn't reference a file.
    """
    import yaml

    with yaml_path.open("r", encoding="utf-8") as f:
        contract = yaml.safe_load(f)

    if contract is None:
        contract = {}

    # Override / create a 'local' server of type parquet
    if "servers" not in contract or not isinstance(contract["servers"], dict):
        contract["servers"] = {}

    contract["servers"]["local"] = {
        "type": "local",
        "path": parquet_absolute_path,
        "format": "parquet",
    }

    with yaml_path.open("w", encoding="utf-8") as f:
        yaml.dump(contract, f, allow_unicode=True, sort_keys=False)


def _serialize_run(run) -> dict:
    """Convert a datacontract RunResult to a JSON-serialisable dict."""
    checks = []
    for check in getattr(run, "checks", []):
        checks.append({
            "name":   getattr(check, "name", None),
            "type":   getattr(check, "type", None),
            "result": getattr(check, "result", None),
            "reason": getattr(check, "reason", None),
            "model":  getattr(check, "model", None),
            "field":  getattr(check, "field", None),
        })

    return {
        "result":      getattr(run, "result", None),
        "checks":      checks,
        "passed":      sum(1 for c in checks if c["result"] == "passed"),
        "failed":      sum(1 for c in checks if c["result"] in ("failed", "error")),
        "warnings":    sum(1 for c in checks if c["result"] == "warning"),
    }
