# This script will create a git tag adding the jenkins build number.
libVersion=v28.2

echo Creating tag...
git tag -a $libVersion.$BUILD_NUMBER -m "$libVersion Build $BUILD_NUMBER"


