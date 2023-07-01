for i in 0 1 2 3 4 5; do
	blkdiscard "/dev/nvme${i}n1";
done;

echo "Reset SSDs"
echo "Preconditioning"

for i in 0 1 2 3 4 5; do
	dcfldd if=/dev/zero of="/dev/nvme${i}n1" obs=4k count=$(echo $(( 2 * $(echo $(( $(blockdev --getsize64 "/dev/nvme${i}n1") / 4096 )) ) )) ) > diskcondition$i.log 2>&1 &
done;
