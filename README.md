# check_certificate
Plugin for Icinga2 to check the expiration of an SSL/TLS certificate.

## Usage
```
check_certificate.py [-h] -D <DOMAIN> [-P <PORT>] [-w <WARN>] [-c <CRIT>] 
                                      [-p] [-v] [-V]

optional arguments:
  -h, --help                        Show this help message
  
  -D <domain>, --domain <domain>    Hostname or ip address
                        
  -P <port>, --port <port>          Set the port to check (default is 443)
                        
  -w <warn>, --warn <warn>          The warning threshold in days
                        
  -c <crit>, --crit <crit>          The critical threshold in days
                        
  -p, --perfdata                    Turns on performance data
  
  -v, --verbose                     Show more output
  
  -V, --version                     Shows the current versiond
```

## Example
### HTTPS
```
./check_certificate.py --domain google.com --warn 14 --crit 3 --perfdata
OK - Certificate is valid until 2019-09-10 08:16:00 (48 days) | 'valid_days'=48;14;3
```

### IMAPS
```
./check_certificate.py --domain imap.gmail.com --port 993 --warn 14 --crit 3
OK - Certificate is valid until 2019-09-10 08:15:00 (48 days)

```

## Icinga2 integration
### Configure the CheckCommand
```
object CheckCommand "check_certificate" {
    command = [ PluginContribDir + "/check_certificate.py"]

    arguments = {
        "-D" = {
            value = "$DOMAIN$"
            description = "The DN of which the certificate should be checked."
            required = true
        }
        "-P" = {
            value = "$PORT$"
            description = "The Port on which to check."
            required = false
        }
        "-w" = {
            value = "$WARNING$"
            description = "The warning threshold in days."
            required = false
        }
        "-c" = {
            value = "$CRITICAL$"
            description = "The critical threshold in days."
            required = false
        }
        "-p" = {
            set_if = "$PERFDATA$"
            description = "Activate performancedata (just for fun)."
            required = false
        }
    }
  
    vars.DOMAIN   = "$DOMAIN$"
    vars.PORT     = "$PORT$"
    vars.WARNING  = "$WARNING$"
    vars.CRITICAL = "$CRITICAL$"
    vars.PERFDATA = "$PERFDATA$"
}
```

### Service definition
#### HTTPS
```
apply Service "CERTIFICATE - www.google.com" {
    import "generic-service"
  
    check_command = "check_certificate"

    vars.DOMAIN   = "www.google.com"
    vars.WARNING  = "30"
    vars.CRITICAL = "15"
    
    assign where match("HOSTNAME", host.name)
}
```

#### IMAPS
```
apply Service "CERTIFICATE - imap.gmail.com" {
    import "generic-service"

    check_command = "check_certificate"

    vars.DOMAIN   = "imap.gmail.com"
    vars.PORT     = "993"
    vars.WARNING  = "7"
    vars.CRITICAL = "3"
    vars.PERFDATA = true

    assign where match("HOSTNAME", host.name)
}
```

#### Alternative
```
var domainlist = {
        "mail.example.tld" = [443, 587, 993],
        "google.com" = [443],
        "example.tld" = [443, 8443]
}
for(domain => ports in domainlist) {
        for(port in ports) {
                apply Service "CERTIFICATE - " + domain + " Port: " + port use(domain, port) {
                        import "generic-service"

                        check_command  = "check_certificate"
                        check_interval = 1d

                        vars.DOMAIN   = domain
                        vars.PORT     = port
                        vars.WARNING  = 7
                        vars.CRITICAL = 2
                        vars.PERFDATA = true

                        assign where match("maui*", host.name)
                }
        }
}
```