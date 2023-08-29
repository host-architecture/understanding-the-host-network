Disable frequency scaling and turbo boost for deterministic measurements
```
sudo ./disable-scaling.sh
```

Disable DDIO (on Cascake Lake)
Using change-ddio.c in ddio-bench repo
Edit `ddio_state=0` and PCIe bus to `0xc8`, `0xc9`, `0xca`, `0xcb`, `0xdb`, `0xdc`. Run the following for each bus/port:
```
gcc change-ddio.c -o change-ddio -lpci; sudo ./change-ddio
```