#!/bin/bash

jfile=members.json
ofile=mp_rfid_report.txt
cdir=$(dirname "$(realpath "$0")")/cache_files
pyfil=$(dirname "$(realpath "$0")")/filter.py
bcfil=$(dirname "$(realpath "$0")")/build_cache2.py

echo "MemberPress vs RFID Report" > $cdir/$ofile
echo >> $cdir/$ofile
echo "Date of report:" `TZ=America/Chicago date` >> $cdir/$ofile

# MemberPress to temp json 'cache' file-----------------------------
echo -n "Getting database info... "
python3 $bcfil > $cdir/$jfile

# Section 1---------------------------------------------------------
# Headings
cat $cdir/$jfile | python3 $pyfil --wrong-active | jq -r '.[0] | to_entries | map(.key) | join(",")' > $cdir/tmp1
# Body
cat $cdir/$jfile | python3 $pyfil --wrong-active | jq -r '.[]| join(",")' > $cdir/tmp2
# Sort body by active_mms (col 3) first, by name (col 2) second
cat $cdir/tmp2 | sort -t , -k3,3 -k6,6 > $cdir/tmp3
# Nicer output
echo >> $cdir/$ofile
echo "Mismatches in Active..." >> $cdir/$ofile
cat $cdir/tmp1 $cdir/tmp3 | column -s , -t >> $cdir/$ofile

# Section 2---------------------------------------------------------
# Headings
cat $cdir/$jfile | python3 $pyfil --wrong-rfid-name | jq -r '.[0] | to_entries | map(.key) | join(",")' > $cdir/tmp1
# Body
cat $cdir/$jfile | python3 $pyfil --wrong-rfid-name | jq -r '.[]| join(",")' > $cdir/tmp2
# Sort body by name (col 2)
cat $cdir/tmp2 | sort -t , -k2,2 > $cdir/tmp3
# Nicer output
echo >> $cdir/$ofile
echo "Active in rfid but no matching name in mms..." >> $cdir/$ofile
cat $cdir/tmp1 $cdir/tmp3 | column -s , -t >> $cdir/$ofile

# Section 3---------------------------------------------------------
# Headings
cat $cdir/$jfile | python3 $pyfil --wrong-name | jq -r '.[0] | to_entries | map(.key) | join(",")' > $cdir/tmp1
# Body
cat $cdir/$jfile | python3 $pyfil --wrong-name | jq -r '.[]| join(",")' > $cdir/tmp2
# Sort body by name (col 2)
cat $cdir/tmp2 | sort -t , -k2,2 > $cdir/tmp3
# Nicer output
echo >> $cdir/$ofile
echo "Active in mms but no matching name in rfid..." >> $cdir/$ofile
cat $cdir/tmp1 $cdir/tmp3 | column -s , -t >> $cdir/$ofile

echo >> $cdir/$ofile
echo "End of Report" >> $cdir/$ofile
