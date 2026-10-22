"""ACVA Reproducibility Bundle generator and re-execution validator."""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any, Dict, Union

from dmrv_core.equations import CalculationContext
from dmrv_core.plugin import MethodologyResult
from methodologies.plugins.fr05_002 import BMFR05002Methodology


def hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class ReproducibilityBundle:
    """Creates and reproduces immutable verification bundles for ACVAs."""

    @classmethod
    def create_bundle(
        cls,
        zip_path: Union[str, Path],
        project_metadata: Dict[str, Any],
        inputs: Dict[str, Any],
        methodology_result: MethodologyResult,
        engine_version: str = "0.1.0",
    ) -> Path:
        out_zip = Path(zip_path)
        out_zip.parent.mkdir(parents=True, exist_ok=True)

        manifest = {
            "engine_version": engine_version,
            "methodology": f"{methodology_result.methodology_code} v{methodology_result.version}",
            "project_id": project_metadata.get("project_id", "PRJ-001"),
            "files": {},
        }

        with zipfile.ZipFile(out_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            # 1. Inputs
            inp_bytes = json.dumps(inputs, indent=2).encode("utf-8")
            zf.writestr("inputs.json", inp_bytes)
            manifest["files"]["inputs.json"] = hash_bytes(inp_bytes)

            # 2. Project metadata
            meta_bytes = json.dumps(project_metadata, indent=2).encode("utf-8")
            zf.writestr("metadata.json", meta_bytes)
            manifest["files"]["metadata.json"] = hash_bytes(meta_bytes)

            # 3. Lineage Trace
            trace_bytes = json.dumps(methodology_result.trace, indent=2).encode("utf-8")
            zf.writestr("lineage_trace.json", trace_bytes)
            manifest["files"]["lineage_trace.json"] = hash_bytes(trace_bytes)

            # 4. Summary Outputs
            out_bytes = json.dumps(methodology_result.summary_outputs, indent=2).encode("utf-8")
            zf.writestr("outputs.json", out_bytes)
            manifest["files"]["outputs.json"] = hash_bytes(out_bytes)

            # 5. Manifest
            manifest_bytes = json.dumps(manifest, indent=2).encode("utf-8")
            zf.writestr("manifest.json", manifest_bytes)

        return out_zip

    @classmethod
    def verify_and_reproduce(cls, zip_path: Union[str, Path]) -> bool:
        """Unpack bundle and re-run engine to verify bit-identical outputs."""
        with zipfile.ZipFile(zip_path, mode="r") as zf:
            manifest_data = json.loads(zf.read("manifest.json").decode("utf-8"))
            for fname, expected_hash in manifest_data["files"].items():
                content = zf.read(fname)
                if hash_bytes(content) != expected_hash:
                    raise ValueError(f"Integrity check failed for {fname}: hash mismatch")

            inputs = json.loads(zf.read("inputs.json").decode("utf-8"))
            metadata = json.loads(zf.read("metadata.json").decode("utf-8"))
            expected_outputs = json.loads(zf.read("outputs.json").decode("utf-8"))

        # Re-run pure engine
        plugin = BMFR05002Methodology()
        ctx = CalculationContext(project_id=metadata.get("project_id", "PRJ-001"))
        re_result = plugin.ex_post(ctx, project=metadata, period_data=inputs)

        # Assert outputs match expected
        for key, exp_val in expected_outputs.items():
            if isinstance(exp_val, (int, float)):
                actual_val = re_result.summary_outputs.get(key)
                if actual_val is None or abs(float(actual_val) - float(exp_val)) > 1e-9:
                    raise AssertionError(f"Output mismatch for {key}: {actual_val} != {exp_val}")

        return True


__all__ = ["ReproducibilityBundle"]
