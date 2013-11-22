#!/bin/bash -
#===============================================================================
#
#          FILE:  check_pytomo_running.sh
#
#         USAGE:  ./check_pytomo_running.sh
#
#   DESCRIPTION:  Check pytomo is running by inspecting the date of the last DB
#                   entry
#       OPTIONS:  ---
#  REQUIREMENTS:  ---
#          BUGS:  ---
#         NOTES:  ---
#        AUTHOR: Louis Plissonneau (LP), louis.plissonneau@a3.epfl.ch
#       COMPANY: Orange Labs
#       CREATED: 03/05/2013 13:31:33 CEST
#      REVISION:  ---
#===============================================================================

set -o nounset                              # Treat unset variables as an error

die() {
    err=$1
    shift
    printf "%s\n" "$*"
    exit $err
}

MAX_TIME_DIFFERENCE=600

database_dir=$1
db_file=${database_dir}/`ls -rt $database_dir | tail -1`
table=`sqlite3 $db_file ".tables"`
last_entry_date=`sqlite3 $db_file "select max(ID) from $table"`
last_entry_date=`date --date="$last_entry_date" +%s`
current_date=`date +%s`

time_difference=`echo $(($current_date - $last_entry_date))`
#echo $time_difference

if [ $time_difference -gt $MAX_TIME_DIFFERENCE ]
then
    echo "relaunch script"
    kill_cmd="`ps -ef | grep python | grep Pytomo/start_ | awk '{print $2}' | kill`"
    echo $kill_cmd
    eval $kill_cmd
    #python /home/capture/pytomo/linux_helpers/check_pytomo_running.py
else
    echo "ok"
fi

