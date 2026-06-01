# HQC Hardware Simulation Setup — WSL + Vivado 2025.2

## Environment
- Windows 11 25H2
- WSL2 with Ubuntu 24.04
- Vivado 2025.2 installed inside WSL at /tools/Xilinx/2025.2

## One-time WSL setup steps required beyond defaults

1. Install Python compatibility:
   sudo apt install -y python-is-python3

2. Install ncurses compatibility symlinks (Vivado needs libncurses.so.5,
   Ubuntu 24 only ships .so.6):
   sudo apt install -y libncurses6 libtinfo6
   sudo ln -s /usr/lib/x86_64-linux-gnu/libncurses.so.6 /usr/lib/x86_64-linux-gnu/libncurses.so.5
   sudo ln -s /usr/lib/x86_64-linux-gnu/libtinfo.so.6 /usr/lib/x86_64-linux-gnu/libtinfo.so.5

3. Set locale (Vivado expects en_US.UTF-8):
   sudo dpkg-reconfigure locales
   # select en_US.UTF-8 UTF-8, set as default

4. Run installLibs.sh after Vivado install:
   sudo /tools/Xilinx/2025.2/Vivado/scripts/installLibs.sh

5. Add Vivado settings to ~/.bashrc:
   source /tools/Xilinx/2025.2/Vivado/settings64.sh

## Running the keygen simulation

The repo's Makefile dependency chain has a bug: `run_xilinx_sim_keygen`
depends on `build_keygen`, which uses bare `mkdir` (fails if dir exists).
Workaround — run the build once, then call Vivado directly:

   PK=$(openssl rand -hex 40)
   SK=$(openssl rand -hex 40)
   make build_keygen pk_seed=$PK sk_seed=$SK

   # If you need to rerun, first:
   make clean

   # Then to run sim without re-triggering build_keygen:
   mkdir -p ./build/keygen/output
   vivado -mode batch -nojournal -nolog -notrace -source ./build/keygen/tb/keygen.tcl

## Notes on the seed_align.py mystery

The keygen and joint_design targets use DIFFERENT versions of seed_align.py:
- hardware/keygen/memory_files/seed_align.py uses 2 arguments (seed, filename)
- hardware/encap/memory_files/seed_align.py uses 4 arguments (seed, bytes, filename, endianess)

The Makefile is already correct for both. Don't add the "40" and "yes" args
to the keygen call — the keygen script ignores them and writes output to a
file literally named "40".

## Output files

After running, output files appear in:
test_keygen/test_keygen.sim/sim_1/behav/xsim/
Including: S_output_*.out, X_output_*.out, Y_output_*.out,
vect_set_rand_output_*.out, plus binary memory dumps h_*.in, s_*.in,
x_*.in, y_*.in (which feed encap and decap).

## Date and seed values from first successful run
Date: 2026-05-19
PK seed: <5dc305554617108ab43c0c731a03e85b1647b580213998a774ed8b34fde1f1cf355de78fa97d76c7>
SK seed: <e728e9b0de93c833cbc3e6394df2e9148c26ac5fa6bcc368c10bcccf2cf6c7e5f19fe527140db1c6>

A note on seed reproducibility
These seeds were generated randomly by openssl rand -hex 40, so they're unique to the specific run. 
If anyone else uses the same seeds with the same Verilog code, they should get identical output — 
that's the deterministic property of HQC. 
Useful for:
Reproducing bugs
Comparing your outputs against a reference (e.g., the HQC software implementation)



