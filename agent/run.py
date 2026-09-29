"""Explicit entry point for FPGA optimization or ASIC synthesis measurement."""
import argparse
import sys


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', required=True, choices=('fpga', 'asic'))
    parser.add_argument('--synth-tool', choices=('vivado', 'genus', 'dc'))
    parser.add_argument('--design')
    parser.add_argument('--config')
    parser.add_argument('--dispatch', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args(argv)
    if args.target == 'fpga':
        if args.synth_tool not in (None, 'vivado') or args.config:
            parser.error('FPGA uses Vivado and the existing --design registry')
        from . import chip_orchestrator
        if args.design not in chip_orchestrator.DESIGNS:
            parser.error('Choose --design from: ' + ', '.join(chip_orchestrator.DESIGNS))
        if args.dry_run:
            print('FPGA command:', 'python3 agent/chip_orchestrator.py', args.design,
                  '--dispatch' if args.dispatch else '')
            return 0
        return chip_orchestrator.main([args.design] + (['--dispatch'] if args.dispatch else []))
    if args.synth_tool == 'vivado' or args.dispatch or args.design:
        parser.error('ASIC is fixed-period measurement only: use --config and genus or dc')
    if not args.config:
        parser.error('ASIC requires --config')
    from . import asic_synthesis
    options = ['--config', args.config]
    if args.synth_tool:
        options += ['--tool', args.synth_tool]
    if args.dry_run:
        options += ['--dry-run']
    return asic_synthesis.main(options)


if __name__ == '__main__':
    sys.exit(main())
