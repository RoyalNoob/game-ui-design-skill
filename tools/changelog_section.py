#!/usr/bin/env python3
"""Print the CHANGELOG.md section for one version. Usage: python3 tools/changelog_section.py 0.3.1"""
import re, sys
text = open("CHANGELOG.md", encoding="utf-8").read()
m = re.search(rf"^## \[?{re.escape(sys.argv[1])}\]?.*?\n(.*?)(?=^## |\Z)", text, re.S | re.M)
print(m.group(1).strip() if m else f"No changelog entry for {sys.argv[1]}.")
