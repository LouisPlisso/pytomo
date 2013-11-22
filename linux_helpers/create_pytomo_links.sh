#!/bin/bash
#===============================================================================
#
#          FILE:  create_pytomo_links.sh
#
#         USAGE:  ./create_pytomo_links.sh VERSION SERVICE
#
#   DESCRIPTIONi: untar Pytomo archive in youtube and dailymotion dirs and
#                 create links to the databases directory and the Pytomo dir
#                 /home/capture/pytomo
#                                       Pytomo-x.y.z.tar.gz
#                                       youtube
#                                               Pytomo -> Pytomo-x.y.z
#                                                       databases -> /home/capture/databases/youtube
#                                       dailymotion
#                                               Pytomo -> Pytomo-x.y.z
#                                                       databases -> /home/capture/databases/dailymotion
#                                       databases
#                                               youtube
#                                               dailymotion
#
#       OPTIONS:  ---
#  REQUIREMENTS:  ---
#          BUGS:  ---
#         NOTES:  To run in the /home/capture/pytomo directory where the Pytomo archive should be
#        AUTHOR: Ana Oprea
#       COMPANY: Orange Labs
#       CREATED: 08/11/2012 02:23:48 PM CET
#      REVISION:  ---
#===============================================================================


function check_return_code () {
    CMD=$1
    $CMD
    if [ $? -eq 0 ]
    then
        echo "Command *$CMD* executed successfully"
    else
        echo "Command *$CMD* failed. Stopping script execution..."
        exit 1
    fi
}

if [ $# -ne 2 ]
then
    echo "Usage: $0 x.y.z {youtube, dailymotion}"
    exit 1
fi

usage

VERSION=$1
SERVICE=$2
BASE_PATH='/home/capture/'
PYTOMO_DIR_PATH=$BASE_PATH"pytomo/"
PYTOMO_PKG='Pytomo'
DB_DIR='databases'
LOG_DIR='logs'
EXTRACTED_ARCHIVE_PATH="$PYTOMO_DIR_PATH""$SERVICE""/""$PYTOMO_PKG""-""$VERSION"
echo "EXTRACTED_ARCHIVE_PATH = " $EXTRACTED_ARCHIVE_PATH
PYTOMO_PKG_LINK_PATH="$PYTOMO_DIR_PATH""$SERVICE""/""$PYTOMO_PKG"
echo "PYTOMO_PKG = " $PYTOMO_PKG_LINK_PATH
DB_DIR_PATH="$BASE_PATH""$DB_DIR""/""$SERVICE"
echo "DB_DIR_PATH = " $DB_DIR_PATH
PYTOMO_DB_LINK_PATH="$PYTOMO_DIR_PATH""$SERVICE""/""$PYTOMO_PKG""/""$DB_DIR"
echo "PYTOMO_DB_LINK_PATH = " $PYTOMO_DB_LINK_PATH
LOG_DIR_PATH="$BASE_PATH""$LOG_DIR""/""$SERVICE"
echo "LOG_DIR_PATH = " $LOG_DIR_PATH
PYTOMO_LOG_LINK_PATH="$PYTOMO_DIR_PATH""$SERVICE""/""$PYTOMO_PKG""/""$LOG_DIR"
echo "PYTOMO_LOG_LINK_PATH = " $PYTOMO_LOG_LINK_PATH

# tar -xzvf Pytomo-1.9.11.tar.gz -C dailymotion/
check_return_code "tar -xzvf Pytomo-$VERSION.tar.gz -C $SERVICE/"
# ln -snf /home/capture/pytomo/dailymotion/Pytomo-1.9.11/ /home/capture/pytomo/dailymotion/Pytomo
check_return_code "ln -sfn $EXTRACTED_ARCHIVE_PATH $PYTOMO_PKG_LINK_PATH"
# ln -s /home/capture/databases/dailymotion/ /home/capture/pytomo/dailymotion/Pytomo/databases
check_return_code "ln -s $DB_DIR_PATH $PYTOMO_DB_LINK_PATH"
# ln -s /home/capture/logs/dailymotion/ /home/capture/pytomo/dailymotion/Pytomo/logs
check_return_code "ln -s $LOG_DIR_PATH $PYTOMO_LOG_LINK_PATH"
