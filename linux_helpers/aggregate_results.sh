#!/bin/bash -
#===============================================================================
#
#          FILE:  aggregate_results.sh
#
#         USAGE:  ./aggregate_results.sh incoming_dir
#
#   DESCRIPTION:  Aggregate all the incoming results and put them in text file
#
#       OPTIONS:  ---
#  REQUIREMENTS:  ---
#          BUGS:  ---
#         NOTES:  ---
#        AUTHOR: Louis Plissonneau (LP), louis.plissonneau@a3.epfl.ch
#       COMPANY: Orange Labs
#       CREATED: 25/01/2013 08:54:26 CET
#      REVISION:  ---
#===============================================================================

set -o nounset                              # Treat unset variables as an error

die() {
    err=$1
    shift
    printf "%s\n" "$*"
    exit $err
}

treat_files() {
    out_file=$1
    shift
    # clean out_file
    rm -f $out_file
    for f in $*
    do
        #db_file=`tar tjf $f | grep database`
        db_file=$f
    #db_rc=$?
    #if [ $db_rc -eq 0 ]
        #then
        #tar xjf $f $db_file
        table=`sqlite3 $db_file ".tables"`
        sqlite3 $db_file "select * from $table" >> $out_file
        rm $db_file
        #else
            #echo file corrupted: $f
        #fi
    done
}

incoming_dir=$1
OUT_DIR="sylvain"
FILE_PATTERN="ATS-VM-"
LOCATION_LIST="MARS IVRY"

PYTOMO_DB_DIR="pytomo_db_dir"
PYTOMO_DB_DIR="databases"

DATE_FORMAT="%Y-%m-%d"

FIRST_DAY=$2
LAST_DAY=$3

cd $incoming_dir
mkdir -p $OUT_DIR
cd $PYTOMO_DB_DIR

for location in $LOCATION_LIST
do
    readable_incoming_files=""
    for d in `seq $FIRST_DAY $LAST_DAY`
    do
        day=`date --date="$d day ago" +$DATE_FORMAT`
        #day_files=`ls ${FILE_PATTERN}${location}*.${day}.*.tbz`
        day_files=`ls ${FILE_PATTERN}${location}*.${day}.*.db`
        ls_rc=$?
        if [ $ls_rc -eq 0 ]
        then
            for f in $day_files
            do
                if [ -r $f ]
                then
                    readable_incoming_files="$f $readable_incoming_files"
                else
                    echo "$f not readable"
                fi
            done
        else
            echo "no incoming files found on day $day"
        fi
    done
    if test -n "$readable_incoming_files"
    then
        #date=$(date +"%Y%m%d%H%M%s")
        first_date=`date --date="$LAST_DAY day ago" +$DATE_FORMAT`
        last_date=`date --date="$FIRST_DAY day ago" +$DATE_FORMAT`
        out_file="aggregation_sylvain_${location}_from_${first_date}_to_${last_date}.txt"
        treat_files $out_file $readable_incoming_files
        echo start zippping for location $location
        zip ${out_file}.zip $out_file
        rm $out_file
        mv ${out_file}.zip ../$OUT_DIR
    fi
done

