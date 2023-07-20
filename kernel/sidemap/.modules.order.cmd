cmd_/home/midhul/mio/kernel/sidemap/modules.order := {   echo /home/midhul/mio/kernel/sidemap/sidemap.ko; :; } | awk '!x[$$0]++' - > /home/midhul/mio/kernel/sidemap/modules.order
