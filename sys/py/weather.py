import python_weather

import asyncio
import os

async def getweather(city = 'Wuhan'):
  resmsg = ""
  # declare the client. the measuring unit used defaults to the metric system (celcius, km/h, etc.)
  async with python_weather.Client(unit=python_weather.IMPERIAL) as client:
    # fetch a weather forecast from a city
    weather = await client.get(city)
    
    # returns the current day's forecast temperature (int)
    resmsg += "current temperature is" +  str(weather.current.temperature) + "\n"
   # print(weather.current.temperature)
    
    # get the weather forecast for a few days
    for forecast in weather.forecasts:
      resmsg += str(forecast) + "\n"
      #print(forecast)
      
      # hourly forecasts
      for hourly in forecast.hourly:
        resmsg += f' --> {hourly!r}' + "\n"
       # print(f' --> {hourly!r}')
  return resmsg
def weather():
  # see https://stackoverflow.com/questions/45600579/asyncio-event-loop-is-closed-when-getting-loop
  # for more details
  if os.name == 'nt':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
  res = asyncio.run(getweather())
  #print(res)
  return res