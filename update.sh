#! /bin/bash -e

BRANCH=${1:-main}
URL="https://www.github.com/cgspeck/bcoem-score-upload/archive/refs/heads/${BRANCH}.zip"

echo -e "Score uploader update script"
echo -e "\nSelected branch: ${BRANCH}\n"
echo -e "This will download the archive from '${URL}', unzip it, and copy the files present in the zip over those in the current directory\n"

# many ways to skin a cat!
# https://stackoverflow.com/questions/226703/how-do-i-prompt-for-yes-no-cancel-input-in-a-linux-shell-script
echo "Do you wish to continue?"
select yn in "Yes" "No"; do
    case $yn in
        Yes ) break;;
        No ) exit;;
    esac
done

cleanup() {
    echo "Cleaning up...removing $TMP"
    rm -rf "$TMP"
    # https://medium.com/@dirk.avery/the-bash-trap-trap-ce6083f36700
    if [ "$1" != "0" ]; then
        # error handling goes here
        echo "Error $1 occurred on $2"
    fi
}

TMP=$(mktemp -d)
trap 'cleanup $? $LINENO' EXIT

ZIP_DEST="${TMP}/update.zip"
echo "Using temporary directory: ${TMP}"
echo "Downloading zip..."
curl -Lo "${ZIP_DEST}" "${URL}"
echo "Uncompressing archive..."
unzip "$ZIP_DEST" -d "$TMP"
echo "Copying files across..."
FROM="$TMP/bcoem-score-upload-$BRANCH/."
TO="."
cp -r "${FROM}" "${TO}"
echo -e "\nYou may have to restart the python application for your changes to take effect\n"
