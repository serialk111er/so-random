import requests
import random
from bs4 import BeautifulSoup
from datetime import date
from datetime import timedelta
from cs50 import SQL


def get_date(lastDrawn):
    """Detirmines if the current date is after the date of the last known draw"""
    last = date.fromisoformat(lastDrawn)    # Create date object from string
    next = last + timedelta(days=7)         # Calculate date of next draw
    today = date.today()                    # Get todays date
    
    if today > next:
        return True
    else:
        return False


def aggregate(db, weeks):
    # Respective hot/cold thresholds
    normalMedian = 11 #10
    powerMedian = 3 #3
    
    # Initialize arrays for hot and cold ball trackers
    global coldNumbers
    global hotNumbers
    global coldPowers
    global hotPowers
    coldNumbers = []
    hotNumbers = []
    coldPowers = []
    hotPowers = []

    # Count number of times each ball is drawn
    global numbers
    global powers
    numbers = {}
    powers = {}
    # Sets counters to 0
    for n in range(1,36):
        if n <= 20:
            numbers[str(n)] = 0
            powers[str(n)] = 0
        else:
            numbers[str(n)] = 0

    # Get past years draws for current heat
    pool = db.execute("SELECT numbers, powerball FROM results ORDER BY drawDate DESC LIMIT ?", weeks)

    # Delete first record (most recent result) for the previous weeks results
    if (weeks == 53):
        del(pool[0]) 

    # Count ball draw occurances
    for draw in pool:
        nums = draw['numbers'].split(',')
        power = draw['powerball']
        for n in nums:
            if n in numbers:
                numbers[n] = numbers[n] + 1
        if power in powers:
            powers[power] = powers[power] + 1

    # Divide balls into hot and cold arrays
    # Normal balls
    for value in numbers:
        if numbers[value] > normalMedian - 1:
            if value not in hotNumbers:
                hotNumbers.append(value)
        elif value not in coldNumbers:
            coldNumbers.append(value)
        
    # Power balls
    for value in powers:
        if powers[value] > powerMedian - 1:
            if value not in hotPowers:
                hotPowers.append(value)
        elif value not in coldPowers:
            coldPowers.append(value)

    # Return collection of aggregates
    aggregates = {}
    aggregates['coldNumbers'] = coldNumbers
    aggregates['hotNumbers'] = hotNumbers
    aggregates['coldPowers'] = coldPowers
    aggregates['hotPowers'] = hotPowers

    # Clears number tracking arrays for use on the next run
    if (weeks == 53):
        coldNumbers = []
        hotNumbers = []
        coldPowers = []
        hotPowers = []

    return aggregates


def dbUpdate(URL, db):
    """Scrape results and update db"""
    # Check if latest results have already been inserted
    lastDrawn = db.execute("SELECT MAX(drawDate) AS drawDate FROM results")[0]['drawDate']
    
    if get_date(lastDrawn):
        print("Updating database")

        # Get html content, setup BeautifulSoup object
        page = requests.get(URL)
        soup = BeautifulSoup(page.content, "html.parser")
        
        # Remove ads from results table
        for ad in soup.find_all("tr", {'class':'noBox'}): 
            ad.decompose()
        
        # Find element by html id tag, get all tr elements & delete table header
        results = soup.find(id="content")
        draws = results.find_all('tr')
        # Remove header
        del(draws[0])

        # Parse data from html tags
        for draw in draws:
            # Refactor date for SQL insertion
            rawDate = draw.find('a', href=True)['href']
            date = rawDate[19:]
            d = date[0:2]
            m = date[3:5]
            y = date[6:]
            cleanDate = f"{y}-{m}-{d}"
            print(cleanDate)

            # Extract drawn numbers from soup
            rawNumbers = draw.find_all("li", class_="result medium pb ball dark ball")
            powerball = draw.find("li", class_="result medium pb ball dark powerball").text
            numbers = []
            
            for number in rawNumbers:
                numbers.append(number.text)
            
            numString = ','.join(numbers)
            
            # Insert into db if not present
            dbDates = db.execute("SELECT drawDate FROM results")
            listedDates = []

            for date in dbDates:
                listedDates.append(date['drawDate'])

            if cleanDate not in listedDates:
                db.execute("INSERT INTO results (numbers, powerball, drawDate) VALUES (:n, :p, :date)", 
                n=numString, p=powerball, date=cleanDate)
    else:
        print("Database up to date")


# Draw normal balls based on hotness
def drawBall(code):
    while True:
        n = random.randint(1,35)
        if code == 'h' and n in hotNumbers:
            break
        elif code == 'c' and n in coldNumbers:
            break
        elif code == 'r':
            break
    return n


# Draw power balls based on hotness
def drawPower(code):
    while True:
        n = random.randint(1,20)
        if code == 'h' and n in hotPowers:
            break
        elif code == 'c' and n in coldPowers:
            break
        elif code == 'r':
            break
    #print(f"Power = {n}")
    return n


def changeState():
    # This function changes the array values from str to their int counterpart
    arrays = [hotNumbers, coldNumbers, hotPowers, coldPowers]
    for array in arrays:
        count = 0
        while count != len(array):
            array[count] = int(array[count])
            count += 1


def getLastDraw(db):
    # Get numbers from last draw
    numbers = {}
    lastDraw = db.execute("SELECT numbers, powerball FROM results ORDER BY drawDate DESC LIMIT 1")
    
    nums =  lastDraw[0]['numbers'].split(',')
    numbers['lastNums'] = nums
    numbers['lastPower'] = lastDraw[0]['powerball']

    return numbers