#!/usr/bin/env bash
# Puts the APK the prompt names in the workspace, so the run spends its turns routing, not searching for the file.
# A zip header is enough: the case grades only whether the skill fires.
set -euo pipefail
printf 'PK\003\004' > shop-release.apk
