Compile
```
gcc -o poll_banks poll_banks.c
```

Run bank load monitoring (runs for 10 secs)
```
sudo taskset -c 31 ./poll_banks
```

Get CDF of bank deviation
```
cat log.bconf | awk 'NR > 1 {b1 += $4; b2 += $5; b3 += $6; b4 += $7; if(NR%100 == 0) { bmax=0; if(b1 > bmax) {bmax = b1;} if(b2 > bmax) {bmax = b2;} if(b3 > bmax) {bmax=b3;} if(b4 > bmax) {bmax = b4;} bavg=(b1+b2+b3+b4)/4; print bmax/bavg; b1=0;b2=0;b3=0;b4=0; }}' | sort -n | awk '{print $1, NR/10000}' > ~/membw-eval/random-cores1.bankcdf.txt
```