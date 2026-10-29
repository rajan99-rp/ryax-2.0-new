from pathlib import Path
import random

source = Path("combined_dataset.txt")
text = source.read_text(encoding="utf-8")

# Har conversation ka ending marker validate karo.
parts = text.split("### End")
examples = [p.strip() for p in parts if p.strip()]

valid = []
for example in examples:
    if "### User:" not in example or "### RayX:" not in example:
        print("Skipped malformed example:", repr(example[:60]))
        continue
    valid.append(example + "\n\n### End\n")

if len(valid) < 5:
    raise SystemExit("Bahut kam valid examples hain. Dataset check karo.")

random.Random(42).shuffle(valid)

# Small datasets ke liye 20% validation examples.
n_val = max(1, int(len(valid) * 0.2))
validation = valid[:n_val]
training = valid[n_val:]

Path("train.txt").write_text(
    "\n".join(training), encoding="utf-8"
)
Path("validation.txt").write_text(
    "\n".join(validation), encoding="utf-8"
)

print("Total conversations:", len(valid))
print("Training conversations:", len(training))
print("Validation conversations:", len(validation))
print("Created train.txt and validation.txt")
