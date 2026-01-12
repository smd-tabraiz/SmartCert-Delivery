import os
import csv
import shutil

def clean_name(name):
    return name.strip().replace(" ", "_")

def rename_certificates(csv_file, original_folder, renamed_folder):
    os.makedirs(renamed_folder, exist_ok=True)

    with open(csv_file, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        # Normalize headers
        headers = [h.strip().lower() for h in reader.fieldnames]
        reader.fieldnames = headers

        # Auto-detect filename column
        filename_col = None
        for h in headers:
            if h in ("filename", "file", "file_name"):
                filename_col = h
                break

        for index, row in enumerate(reader, start=1):
            name = clean_name(row["name"])
            filename_value = (row.get(filename_col) or "").strip() if filename_col else ""
            found = False

            # 1️⃣ filename logic
            if filename_value:
                # numeric mapping
                if filename_value.isdigit():
                    for ext in [".jpg", ".jpeg", ".png", ".pdf"]:
                        src = os.path.join(original_folder, f"{filename_value}{ext}")
                        if os.path.exists(src):
                            dst = os.path.join(renamed_folder, f"{name}{ext}")
                            shutil.copy(src, dst)
                            found = True
                            break
                # exact filename
                else:
                    src = os.path.join(original_folder, filename_value)
                    if os.path.exists(src):
                        _, ext = os.path.splitext(filename_value)
                        dst = os.path.join(renamed_folder, f"{name}{ext}")
                        shutil.copy(src, dst)
                        found = True

            # 2️⃣ fallback index
            if not found:
                for ext in [".jpg", ".jpeg", ".png", ".pdf"]:
                    src = os.path.join(original_folder, f"{index}{ext}")
                    if os.path.exists(src):
                        dst = os.path.join(renamed_folder, f"{name}{ext}")
                        shutil.copy(src, dst)
                        found = True
                        break

            if not found:
                print(f"❌ Missing certificate for row {index} ({row.get('name')})")
