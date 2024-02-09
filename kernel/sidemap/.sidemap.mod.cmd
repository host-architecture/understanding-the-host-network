savedcmd_/home/midhul/mio/kernel/sidemap/sidemap.mod := printf '%s\n'   sidemap.o | awk '!x[$$0]++ { print("/home/midhul/mio/kernel/sidemap/"$$0) }' > /home/midhul/mio/kernel/sidemap/sidemap.mod
