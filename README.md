# jcparsers custom filters

~~~
git clone https://github.com/zzOzz/jcparsers $HOME/.local/share/jc/jcparsers
~~~

## ufwlog 

String input example
~~~
journalctl -k --since "1 day ago" -o json| jq -r '{ time: ((.__REALTIME_TIMESTAMP|tonumber)/1000/1000|todate), message:.MESSAGE}|@json' | jc --ufwlog


journalctl -k --since "1 day ago" -o json|jc --ufwlog | jq '.MESSAGE|@json'
~~~~


Json input example
~~~
journalctl -k --since "1 day ago" -o json| jq -r '.MESSAGE' | jc --ufwlog
~~~



~~~mermaid
mindmap
  root((mindmap))
    Origins
      Long history
      ::icon(fa fa-book)
      Popularisation
        British popular psychology author Tony Buzan
    Research
      On effectiveness<br/>and features
      On Automatic creation
        Uses
            Creative techniques
            Strategic planning
            Argument mapping
    Tools
      Pen and paper
      Mermaid
~~~