# jcparsers custom filters

~~~
git clone https://github.com/zzOzz/jcparsers $HOME/.local/share/jc/jcparsers
~~~

## ufwlog 

String input example
~~~
journalctl -k --since "1 day ago" -o json| jq -r '{ time: ((.__REALTIME_TIMESTAMP|tonumber)/1000/1000|todate), message:.MESSAGE}|@json' | jc --ufwlog
~~~~


Json input example
~~~
journalctl -k --since "1 day ago" -o json| jq -r '.MESSAGE' | jc --ufwlog
~~~