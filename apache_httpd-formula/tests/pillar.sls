apache_httpd:
  modules:
    - status
  sysconfig:
    apache_servername: ipv6-localhost
  configs:
    remote:
      RemoteIPHeader: X-Forwarded-For
      RemoteIPTrustedProxy:
        - 2001:db8::1
        - 2001:db8::2
  vhosts:
    status:
      listen: ipv6-localhost:8181
      Location:
        /server-status:
          SetHandler: server-status
    mysite1:
      Directory:
        /srv/www/htdocs:
          Require: all granted
    mysite2:
      ServerName: mysite2.example.com
      Protocols:
        - h2
        - http/1.1
      Alias:
        /static: /srv/www/static
      Directory:
        /srv/www/static:
          Options:
            - Indexes
            - FollowSymLinks
          AllowOverride: None
          Require: all granted

