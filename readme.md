# TA-laundryview : Splunk Add-on for LaundryView Room Sites

Author: George Starcher (starcher)
Email: george@georgestarcher.com

#Description:

The Splunk Add-on for Laundryview is a modular input that scrapes laundry room data from the mobile version of the page for a given laundry room.

#Requirements:

* Create an index called laundry
* You need to know the laundry room (lr) code for the site you want to scrape data for 

The URL for a site can give you the 'lr' code:
http://laundryview.com/laundry_room.php?lr=698355

#SETUP:

1. Install the TA
2. Create an index (laundry)
3. Create each modular input and point at your index (laundry) with sourcetype (laundry) for each LR code you want to track
4. Set the internal to the cron schedule: */15 * * * *
5. Set the host to laundryview.com

#COMMENTS:

Setting the cron schedule to every 15 minutes is a fair resolution for machine activity without scraping a page too often.

When time charting data use the span=15m so it lines up with the polling interval.

> index=laundry type=washer | timechart span=15 count by inUse


