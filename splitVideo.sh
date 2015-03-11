#!/bin/sh

if [ "$#" -ne 1 ]; then
	echo "Usage: $0 <Moviefile>.mpg"
	exit 1
fi

SCRIPTPATH=$( cd "$( dirname "$0" )" && pwd )

MOVIE=$1
SPLITS=${1%mpg}csv
SPLITDIR=${1%.mpg}_split

if ! [ -e $SPLITS ]; then
	echo "$SPLITS not found"
	exit 1
fi

if ! [ -e $MOVIE ]; then
	echo "$MOVIE not found"
	exit 1
fi

mkdir -p $SPLITDIR

while IFS=, read -r fn st et
do
DURATION=`${SCRIPTPATH}/timeDiff.ruby "$st" "$et"`
#echo $DURATION
#	echo "filename is $fn, start is $st, end is $et"
ffmpeg -ss $st -i $MOVIE -t "$DURATION" -c:v copy -c:a copy ${SPLITDIR}/${fn}.mpg < /dev/null
done < $SPLITS
