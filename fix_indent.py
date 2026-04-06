with open("client_app/ui/main_window.py", "r") as f:
    lines = f.readlines()

out = []
# Skip the initial lines up to the start of extracted methods
# Actually, everything appended was root-level, so we must add 4 spaces
in_append_zone = False
for line in lines:
    if line.startswith("def import_profiles_from_txt(self):") or in_append_zone:
        in_append_zone = True
        if line.strip() == "":
            out.append(line)
        else:
            out.append("    " + line)
    else:
        out.append(line)

with open("client_app/ui/main_window.py", "w") as f:
    f.writelines(out)
