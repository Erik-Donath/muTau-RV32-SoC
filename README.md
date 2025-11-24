# RiscV-SoC
Last Hope

# Use 
to use the Project and the build tools you need to download the gowin-eda from there website and place the IDE Directory in the root Directory of this Project then just run `make env` to build an run the Docker-Container do to this Project is in en experimental state in the Docker-Container type in the CLI `PATH="$PATH:workspace/IDE/bin"` then build the CPU via `python3 cpu.py --build`.
`export PATH="$PATH:/workspace/IDE/bin"`
At the moment you will run into an error:
``` bash
python3 -m litex.soc.software.crcfbigen bios.bin --little
python3 -m litex.soc.software.memusage bios.elf /workspace/build/sipeed_tang_nano_9k/software/bios/../include/generated/regions.ld riscv64-unknown-elf

ROM usage: 27.13KiB 	(21.20%)
RAM usage: 1.64KiB 	(20.51%)

make: Leaving directory '/workspace/build/sipeed_tang_nano_9k/software/bios'
INFO:SoC:Initializing ROM rom with contents (Size: 0x6c98).
INFO:SoC:Auto-Resizing ROM rom from 0x20000 to 0x6c98.
gw_sh: error while loading shared libraries: libGL.so.1: cannot open shared object file: No such file or directory
Traceback (most recent call last):
  File "/workspace/cpu.py", line 136, in <module>
    main()
  File "/workspace/cpu.py", line 124, in main
    builder.build(**parser.toolchain_argdict)
  File "/opt/litex/litex/soc/integration/builder.py", line 416, in build
    vns = self.soc.build(build_dir=self.gateware_dir, **kwargs)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/litex/litex/soc/integration/soc.py", line 1541, in build
    return self.platform.build(self, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/litex/litex/build/gowin/platform.py", line 47, in build
    return self.toolchain.build(self, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/litex/litex/build/generic_toolchain.py", line 123, in build
    self.run_script(script)
  File "/opt/litex/litex/build/gowin/gowin.py", line 181, in run_script
    raise OSError("Error occured during Gowin's script execution.")
OSError: Error occured during Gowin's script execution.
```
```
```

i guess to fix this issue you have to install the nessasary OpenGL lib (maybe keep in mind that the Dockerfile is using debian bookworm-slim which has a much smaller mirrorlist so maybe change it do debian/bookworm). you have to change the Dockerfile to make this happen.  
