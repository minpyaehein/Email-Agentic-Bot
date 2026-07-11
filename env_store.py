import os

from config import ENV_FILE


def clean_env_value(key, value):
    value = str(value or "").strip()
    value = value.replace("\r", "").replace("\n", "")

    if key == "EMAIL_PASS":
        value = value.replace(" ", "")

    return value


def save_env_updates(updates):
    existing_lines = []

    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            existing_lines = f.readlines()

    written = set()
    new_lines = []

    for line in existing_lines:
        stripped = line.strip()

        if not stripped or stripped.startswith("#") or "=" not in line:
            new_lines.append(line)
            continue

        key = line.split("=", 1)[0].strip()

        if key in updates:
            new_lines.append(f"{key}={updates[key]}\n")
            written.add(key)
        else:
            new_lines.append(line)

    for key, value in updates.items():
        if key not in written:
            new_lines.append(f"{key}={value}\n")

    with open(ENV_FILE, "w", encoding="utf-8") as f:
        f.writelines(new_lines)