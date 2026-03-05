#!/usr/bin/env sh
set -eu

if [ "${1:-}" = "" ]; then
  echo "Uso: ./release.sh <version-semver>"
  exit 1
fi

VERSION="$1"
DATE="$(date +%Y-%m-%d)"

echo "$VERSION" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+$' || {
  echo "Version invalida: $VERSION (usa formato x.y.z)"
  exit 1
}

if git describe --tags --abbrev=0 >/dev/null 2>&1; then
  LAST_TAG="$(git describe --tags --abbrev=0)"
  COMMITS="$(git log --pretty=format:'- %h %s' "$LAST_TAG"..HEAD)"
else
  LAST_TAG=""
  COMMITS="$(git log --pretty=format:'- %h %s')"
fi

[ -n "$COMMITS" ] || COMMITS="- Sin commits desde el ultimo release."

cat > .release_section.tmp <<EOF
## [$VERSION] - $DATE

### Commits
$COMMITS

EOF

if grep -q "^## \[Unreleased\]" CHANGELOG.md; then
  awk 'BEGIN{printed=0}
       /^## \[Unreleased\]/{print; print ""; while ((getline line < ".release_section.tmp") > 0) print line; printed=1; next}
       {print}
       END{if(!printed){while ((getline line < ".release_section.tmp") > 0) print line}}' CHANGELOG.md > .changelog.new
  mv .changelog.new CHANGELOG.md
else
  printf "# Changelog\n\n## [Unreleased]\n\n" > .changelog.new
  cat .release_section.tmp >> .changelog.new
  mv .changelog.new CHANGELOG.md
fi

rm -f .release_section.tmp
printf "%s\n" "$VERSION" > VERSION
echo "Release preparado: $VERSION"
