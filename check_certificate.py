#!/usr/bin/env python3

import argparse
import sys
import idna
from socket import socket
from OpenSSL import SSL
from datetime import datetime

# Constants
__version__ = '1.0.0'

# Parsing arguments
parser = argparse.ArgumentParser(description="Plugin for Icinga2 to check the expiration of an SSL/TLS certificate.")
parser.add_argument("-D", "--domain", metavar="<domain>", required=True, help="The domain of which the certificate should be checked.")
parser.add_argument("-P", "--port", metavar="<port>", required=False, default=443, help="The Port on which to check (default is 443).")
parser.add_argument("-w", "--warn", metavar="<warn>", required=False, default=7, help="The warning threshold in days.")
parser.add_argument("-c", "--crit", metavar="<crit>", required=False, default=3, help="The critical threshold in days.")
parser.add_argument("-p", "--perfdata", action='store_true', default=False, help="Turns on performance data.")
parser.add_argument("-v", "--verbose", action='store_true', required=False, help="Show more output.")
parser.add_argument("-V", "--version", action='version', version='%(prog)s ' + __version__, help="Shows the current version.")
args = parser.parse_args()


# Functions
def get_certificate(domain, port):
    sock = socket()
    sock.connect((domain, port))

    ctx = SSL.Context(SSL.SSLv23_METHOD)
    ctx.check_hostname = False
    ctx.verify_mode = SSL.VERIFY_NONE

    sock_ssl = SSL.Connection(ctx, sock)
    sock_ssl.set_connect_state()
    sock_ssl.set_tlsext_host_name(idna.encode(domain))
    sock_ssl.do_handshake()
    cert = sock_ssl.get_peer_certificate()
    sock_ssl.close()
    sock.close()

    return cert


def calc_valid_days(not_after):
    now = datetime.today()
    delta = not_after - now

    return delta.days


# Main program
def main():
    cert = get_certificate(args.domain, int(args.port))
    cert_crypt = cert.to_cryptography()
    valid_days = calc_valid_days(cert_crypt.not_valid_after)
    perfdata = " | 'valid_days'="+str(valid_days)+";"+str(args.warn)+";"+str(args.crit)
    verbosedata = " ISSUER: " + str(cert_crypt.issuer) + " SUBJECT: " + str(cert_crypt.subject)

    if cert.has_expired():
        msg = "CRITICAL - Certificate has expired on " + str(cert_crypt.not_valid_after) + " (" + str(valid_days) + " days)"
        if args.verbose:
            msg += verbosedata
        if args.perfdata:
            msg += perfdata
        print(msg)
        sys.exit(2)

    if valid_days > int(args.crit):
        if valid_days > int(args.warn):
            msg = "OK - Certificate is valid until " + str(cert_crypt.not_valid_after) + " (" + str(valid_days) + " days)"
            if args.verbose:
                msg += verbosedata
            if args.perfdata:
                msg += perfdata
            print(msg)
            sys.exit(0)
        else:
            msg = "WARNING - Certificate is valid until " + str(cert_crypt.not_valid_after) + " (" + str(valid_days) + " days)"
            if args.verbose:
                msg += verbosedata
            if args.perfdata:
                msg += perfdata
            print(msg)
            sys.exit(1)
    else:
        msg = "CRITICAL - Certificate is valid until " + str(cert_crypt.not_valid_after) + " (" + str(valid_days) + " days)"
        if args.verbose:
            msg += verbosedata
        if args.perfdata:
            msg += perfdata
        print(msg)
        sys.exit(2)


if __name__ == "__main__":
    main()
