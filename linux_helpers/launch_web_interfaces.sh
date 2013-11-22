#!/bin/bash - 
#===============================================================================
#
#          FILE:  launch_web_interfaces.sh
#
#         USAGE:  ./launch_web_interfaces.sh 
#
#   DESCRIPTION:  Launch the web interfaces for both youtube and dailymotion
#                 with gunicorn
#       OPTIONS:  ---
#  REQUIREMENTS:  ---
#          BUGS:  ---
#         NOTES:  ---
#        AUTHOR: Louis Plissonneau (LP), louis.plissonneau@a3.epfl.ch
#       COMPANY: Orange Labs
#       CREATED: 21/10/2013 15:44:19 CEST
#      REVISION:  ---
#===============================================================================

set -o nounset                              # Treat unset variables as an error

die() {
    err=$1
    shift
    printf "%s\n" "$*"
    exit $err
}


BASE_PATH="/home/capture/pytomo"
PYTOMO_PKG="Pytomo"
YT_SERVICE="youtube"
YT_WEB_PORT="5555"
DM_SERVICE="dailymotion"
DM_WEB_PORT="7777"

WEB_START="gunicorn pytomo.webpage:wsgi_app"
GUNICORN_ADDRESS_OPTION="-b 0.0.0.0"

# start youtube
cd ${BASE_PATH}/${YT_SERVICE}/${PYTOMO_PKG}
${WEB_START} ${GUNICORN_ADDRESS_OPTION}:${YT_WEB_PORT} &

# start dailymotion
cd ${BASE_PATH}/${DM_SERVICE}/${PYTOMO_PKG}
${WEB_START} ${GUNICORN_ADDRESS_OPTION}:${DM_WEB_PORT} &

