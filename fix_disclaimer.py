import re

with open("index.html", "r") as f:
    html = f.read()

old_disclaimer = """<strong>Disclaimer:</strong> This email is from ABIZ Global Services, a digital marketing agency providing SEO, web, and app development solutions. If you wish to unsubscribe, please reply with "Unsubscribe"."""
new_disclaimer = """<strong>Disclaimer:</strong> This email is intended for business growth purposes; reply with "Unsubscribe" to opt out."""

if old_disclaimer in html:
    html = html.replace(old_disclaimer, new_disclaimer)
    with open("index.html", "w") as f:
        f.write(html)
    print("Disclaimer shortened.")
else:
    print("Old disclaimer not found.")
