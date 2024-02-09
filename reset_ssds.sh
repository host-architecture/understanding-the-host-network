for i in b c d e f g i; do
	blkdiscard "/dev/sd${i}";
done;

echo "Reset SSDs"
echo "Preconditioning"

for i in b c d e f g i; do
	dcfldd if=/dev/zero of="/dev/sd${i}" obs=4k count=$(echo $(( 2 * $(echo $(( $(blockdev --getsize64 "/dev/sd${i}") / 4096 )) ) )) ) > diskcondition$i.log 2>&1 &
done;
