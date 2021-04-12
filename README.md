[![MIT License][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url]


# GartnerEmailParser
An script to parse the emails from gartnerwebinars@gartner.com

I use this script to extract the webinars details from the marketing email from Gartner to share them in my [blog](https://bigg.blog)
```
python3 GartnerEmailParser.py <url>
```

The URL can be fount at the top of the email you receive is says: "This message contains graphics. If you do not see the graphics, click here to view."

<br>
<img src="https://raw.githubusercontent.com/B1gG/GartnerEmailParser/main/Screenshot_2021-04-12.png" width="90%">

```
positional arguments:
  URL                   url from the gartner email (at the top)

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        configuration file (default: GartnerEmailParser.json)
  -b                    create the bit.ly links using your API details
  -e E [E ...]          exclude specific the months (e.g -e January February)
```
## Config file
It should be a json styled file with the following key/value:
```
{
    "API_USER": "bit_ly_user",
    "API_KEY": "bit_ly_api_key"
}
```
you can find those at [The Bitly API](https://dev.bitly.com/docs/getting-started/introduction) site.
