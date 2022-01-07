## Purpuse

Python script to extend grep command, adding counters, easier to filter by regex group names


## Usage
python3 lg.py *.log *.txt

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
```
