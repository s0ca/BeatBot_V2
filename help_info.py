music_help = ''' 

`!play link/string`
`!pause`
`!resume`
`!next`
`!stop`
`!list`
`!playlist`
`!now`
`!rm int [track index]`
`!rml (remove last entry)`
`!shuffle`
`!vol [0-100]`
'''

ctftime_help = '''

`!ctftime upcoming [1-5]`
return info on a number of upcoming ctfs from ctftime.org

`!ctftime top [year]`
display the leaderboards from ctftime from a certain year.
'''

utility_help = '''
`!magicb [filetype]`
return the magicbytes/file header of a supplied filetype.
`!rot "message"`
return all 25 different possible combinations for the popular caesar cipher - use quotes for messages more than 1 word
`!b64 [encode/decode] "message"`
encode or decode in base64 - if message has spaces use quotations
`!b32 [encode/decode] "message"`
encode or decode in base32 - if message has spaces use quotations
`!binary [encode/decode] "message"`
encode or decode in binary - if message has spaces use quotations
`!hex [encode/decode] "message"`
encode or decode in hex - if message has spaces use quotations
`!url [encode/decode] "message"`
encode or decode based on url encoding - if message has spaces use quotations
`!reverse "message"`
reverse the supplied string - if message has spaces use quotations
`!counteach "message"`
count the occurences of each character in the supplied message - if message has spaces use quotations
`!characters "message"`
count the amount of characters in your supplied message
`!wordcount "phrase"`
count the amount of words in your supplied message
`!atbash "message"`
encode or decode in the atbash cipher - if message has spaces use quotations (encode/decode do the same thing)
`!purge int (default=5)`
remove channel messages
`!whois @nickname`
Whois information about asked user, or yourself if none is specified

'''


help_page = '''

`!help music`
info for all multimedia commands

`!help ctftime`
info for all ctftime commands

`!help utility`
everything else! (basically misc)

`!report/request "an issue or feature"`
report an issue, or request a feature for this Bot
'''


src = "https://www.youtube.com/watch?v=oavMtUWDBTM"
