"""Copy ML charts to docs/charts/ for README embedding."""
import shutil
from pathlib import Path

src = Path("backend/ml/artifacts/charts")
dst = Path("docs/charts")
dst.mkdir(parents=True, exist_ok=True)

for png in src.glob("*.png"):
    shutil.copy2(png, dst / png.name)
    print(f"  ✓ Copied {png.name}")

print(f"\nAll charts copied to {dst}/")
