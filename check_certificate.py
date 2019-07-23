import argparse
import sys
from socket import socket
import idna

from OpenSSL import SSL
from datetime import datetime

# Constants
__version__ = '1.0.0'

# Main program
parser = argparse.ArgumentParser(description="DESCRIPTION v" + str(__version__))
parser.add_argument("-H", "--host", metavar="<host>", required=True, help="Hostname or ip address")
parser.add_argument("-P", "--port", metavar="<port>", required=False, default=443, help="Set the port to check (default is 443)")
parser.add_argument("-w", "--warn", metavar="<warn>", required=False, default=7, help="Value in days for warning alert")
parser.add_argument("-c", "--crit", metavar="<crit>", required=False, default=3, help="Value in days for critical alert")
parser.add_argument("-p", "--perf", action='store_true', default=False, help="Turns on performance data")
parser.add_argument("-v", "--verbose", action='store_true', required=False, help="Show more output")
parser.add_argument("-V", "--version", action='version', version='%(prog)s ' + __version__, help="Shows the version")
args = parser.parse_args()


def get_certificate(hostname, port):
    hostname_idna = idna.encode(hostname)
    sock = socket()
    sock.connect((hostname, port))

    ctx = SSL.Context(SSL.SSLv23_METHOD)
    ctx.check_hostname = False
    ctx.verify_mode = SSL.VERIFY_NONE

    sock_ssl = SSL.Connection(ctx, sock)
    sock_ssl.set_connect_state()
    sock_ssl.set_tlsext_host_name(hostname_idna)
    sock_ssl.do_handshake()
    cert = sock_ssl.get_peer_certificate()
    sock_ssl.close()
    sock.close()

    return cert


def calc_valid_days(notAfter):
    now = datetime.today()
    delta = notAfter - now

    return delta.days


def main():
    cert = get_certificate(args.host, args.port)
    cert_crypt = cert.to_cryptography()
    valid_days = calc_valid_days(cert_crypt.not_valid_after)
    perfdata = " | 'valid_days'="+str(valid_days)+";"+str(args.warn)+";"+str(args.crit)

    if cert.has_expired():
        msg = "CRITICAL - Certificate has expired on " + str(cert_crypt.not_valid_after) + " (" + str(valid_days) + " days)"
        if args.perf:
            msg += perfdata
        print(msg)
        sys.exit(2)

    if valid_days > int(args.crit):
        if valid_days > int(args.warn):
            msg = "OK - Certificate is valid until " + str(cert_crypt.not_valid_after) + " (" + str(valid_days) + " days)"
            if args.perf:
                msg += perfdata
            print(msg)
            sys.exit(0)
        else:
            msg = "WARNING - Certificate is valid until " + str(cert_crypt.not_valid_after) + " (" + str(valid_days) + " days)"
            if args.perf:
                msg += perfdata
            print(msg)
            sys.exit(1)
    else:
        print("CRITICAL - Certificate is valid until " + str(cert_crypt.not_valid_after) + " (" + str(valid_days) + " days)")
        sys.exit(2)


if __name__ == "__main__":
    main()
