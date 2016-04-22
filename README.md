[![Coverage Status](https://coveralls.io/repos/github/nbs-system/nxtool/badge.svg?branch=master)](https://coveralls.io/github/nbs-system/nxtool?branch=master)
[![Code Health](https://landscape.io/github/nbs-system/nxtool/master/landscape.svg?style=flat)](https://landscape.io/github/nbs-system/nxtool/master)
[![Build Status](https://travis-ci.org/nbs-system/nxtool.svg?branch=master)](https://travis-ci.org/nbs-system/nxtool)

```
              __               __ 
 .-----.--.--|  |_.-----.-----|  |
 |     |_   _|   _|  _  |  _  |  |
 |__|__|__.__|____|_____|_____|__|
 
 -- Because life is too short to transform naxsi logs into rules by hand.
```
          
nxtool is a tool to magically transform your [naxsi]( http://naxsi.org ) logs into useful rules.
It can get its data from your elastic instance, or you can feed it flat files,
and it will magically show you some statistics, generate relevant whitelists,
provide type-based rules, ...

Proudly powered by [Python]( https://python.org ) (2 and 3 by the way),
using (optionally) [elasticsearch-dsl]( https://elasticsearch-dsl.readthedocs.org/en/latest/ ),
written with love and tears by the people of [NBS-System] ( https://nbs-system.com ),
nxtools is released under the [GPL]( https://gnu.org/licenses/gpl.html ).