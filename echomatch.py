import asyncio
import maya
import threading

class EchoMatch:
    _global_id = 1

    def __init__(self, details, match_end, loop):
        self.loop = loop
        self.opponent_name = details.group("match_opponent")
        self.raw_time = details.group("match_date") + " " + details.group("match_time")
        self.cb = match_end
        self.match_time = maya.parse(self.raw_time).datetime(to_timezone='Europe/London', naive=False)
        self.timer = self.create_timer()
        self.timer1 = 0
        print("The ID is " + str(EchoMatch._global_id) )
        self.id = EchoMatch._global_id
        EchoMatch._global_id = EchoMatch._global_id + 1
        self.show_match_time()
        self.messageid = 0
        self.fire = True
        print("created match")

    @property
    def global_id(self):
        return self._global_id

    @global_id.setter
    def global_id(self, val):
        self._global_id = val

    def create_timer(self):
        now = maya.now().datetime()
        difference = (self.match_time - now).total_seconds() 
        def f():
            asyncio.run_coroutine_threadsafe(self.cb(self), self.loop)

        #30 minutes before hand
        difference = difference - (45 * 60)
        self.timer = threading.Timer(difference, f) 
        self.timer.start()

        print("created timer")
    
    def show_match_time(self):
        print(self.get_match_string())

    def get_match_string(self):
        time_string = self.match_time.strftime("%A %d/%m @ %H:%M")
        return ("Match ID#{1} [{0}] - " + time_string).format(self.opponent_name, self.id)



