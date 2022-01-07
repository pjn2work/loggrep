## Purpuse

Python script to extend grep command, adding counters, easier to filter by regex group names


## Usage
python lg.py *.log *.txt -r 1

```
  --help	shows this help screen
  --h       shows this help screen
  
  --i 		Case insensitive (not default)
  --m 		Multiline regex (not default/future use)

  --nc		No Counters (not default)
  -c  		Define Counters, ex: -c "-myGroupName1 -otherGroupName2 -gn3"

  --nh		No Header on output (not default)
  --0 		No output (not default)
  --1 		Full line output (default)
  -o  		Define output format, ex: -o "%LINENUMBER% - %myGroupName1% \n\t %gn3%"

  -f  		/full/path/to/foldername/ (default is .)
  filename or file filters, as many as you want

  --sr 		Show regex patterns stored in file
  -rp 		Regex Pattern ( default is ^(?P<all>.*)$ )
  -r  		Regex Pattern line_number from loggrep_patterns.txt file

      		Filter by group names defined in regex pattern, they are converted into parameters, as ex:
  -myGroupName1 ERROR
  -otherGroupName2 ".*My Text Tag.*"


  examples:
    $ python lg.py --sr
    This will show all regex pattern stored on regex file
    
    $ python lg.py -r 1 *.log *.txt /my/folder/file.log -level WARN -c "class" --0
    This will show only counters for class from all log and txt files 
    and also from /my/folder/file.log, where the level is equal to WARN,
    based on regex pattern stored in line 1
    
    $ tail -100 file.log | python lg.py -rp "^(?P<level>[A-Z]{4,5}) (?P<class>.+?) - (?P<msg>.+)$" -o "failed - %class%" --nh --nc
    This will format the output to be like "failed - com.org.my.class" and ommit counters and header
```
