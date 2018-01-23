import sys
import re
import serial
import argparse

def sync(device, retries=5):
    sys.stdout.write('Synchronizing serial interface...')
    sys.stdout.flush()

    # todo: randomize
    sync_pattern = '----synchronize----'
    while retries > 0:
        device.write('echo {}\n'.format(sync_pattern))
        while True:
            line = device.readline()
            if line.strip() == sync_pattern:
                print(' OK')
                return
            if not line:
                break

        retries -= 1
        sys.stdout.write('+')
        sys.stdout.flush()


def cmd_dump(device, args):
    print('Dumping {:d} bytes starting at 0x{:x} ...'.format(
        args.size, args.addr))
    device.write('md.b {:x} {:x}\n'.format(args.addr, args.size))
    device.readline()

    pattern = re.compile(
        '(?P<addr>[0-9a-fA-F]{8}):(?P<data>(\s[0-9a-fA-F][0-9a-fA-F]){0,16})')
    addr = args.addr
    indata = 0

    with open(args.outfile, 'w') as outfile:
        while indata < args.size:
            if indata % 1000 == 0:
                sys.stdout.write('-> {:d} bytes read\r'.format(indata))
                sys.stdout.flush()
            line = device.readline()
            m = pattern.match(line)
            if not m:
                print('Error: invalid line received [{}]'.format(line.strip()))
                return
            if addr != int(m.group('addr'), 16):
                print('Error: invalid address received')
                return
            data = bytearray.fromhex(m.group('data'))
            outfile.write(data)
            addr += len(data)
            indata += len(data)

    # Write file
    print('')
    print('-> Finished writing {}'.format(args.outfile))

def parse_addr(val):
    return int(val, 16)

def parse_len(val):
    return int(val, 0)

def main():
    parser = argparse.ArgumentParser(
        description='U-Boot tool')
    parser.add_argument(
        '--device', default='/dev/ttyUSB0',
        help='Serial device to use')
    parser.add_argument(
        '--baudrate', default=115200,
        help='Baud rate to use')

    subparsers = parser.add_subparsers(
        title='Commands',
        description='Tool commands')

    dump_parser = subparsers.add_parser(
        'dump',
        help='Dump flash (or memory)')
    dump_parser.add_argument('--addr',
                             required=True, type=parse_addr,
                             help='Start address (hexadecimal)')
    dump_parser.add_argument('--size',
                             required=True, type=parse_len,
                             help='Number of bytes to dump')
    dump_parser.add_argument('--outfile', default='dump.bin',
                             help='Name of output file')
    dump_parser.set_defaults(cmd=cmd_dump)
    args = parser.parse_args()

    # Open port
    try:
        device = serial.Serial(port=args.device, baudrate=args.baudrate,
                               timeout=1)
    except Exception as err:
        print('Error: %s' % err)
        #sys.exit(1)

    sync(device)
    args.cmd(device, args)

if __name__ == '__main__':
    main()
