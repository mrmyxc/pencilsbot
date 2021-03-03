import maya
import time
from datetime import datetime, timedelta
import threading

class EchoMatch:
    _global_id = 1

    def __init__(self, details, on_match_end, loop):
        self.loop = loop
        self.opponent_name = details.group("match_opponent")
        self.raw_time = details.group("match_date") + " " + details.group("match_time")
        self.on_match_end = on_match_end
        self.match_time = self.parse_time()
        self.absolute_time = self.match_time.strftime("%d/%m/%Y %H:%M")
        self.timer = self.create_timer()
        self.id = 0
        self.messageid = 0
        self.fire = True
        self.stop = False

        if "match_id" in details.groupdict():
            print("match id is given in saved file")
            self.id = int(details.group("match_id"))
            if self.id >= EchoMatch._global_id:
                EchoMatch._global_id = self.id + 1
            # saved matches also contain messageids
            self.messageid = int(details.group("msg_id"))
            print(f"got message id {self.messageid}")
        else:
            print("match id was not given, allocate")
            self.id = EchoMatch._global_id
            EchoMatch._global_id = EchoMatch._global_id + 1
                
        print("The ID is " + str(self.id) )
        self.show_match_time()
        print("created match")

    @property
    def global_id(self):
        return self._global_id

    @global_id.setter
    def global_id(self, val):
        self._global_id = val

    def create_timer(self):
        MINUTES = 45
        now = maya.now().datetime()
        difference = (self.match_time - now).total_seconds() 
        difference = difference - (MINUTES * 60)
        self.timer = threading.Thread(target=self.exec_every_n_seconds, args=(30, self.check_time_expired, self))
        self.timer.start()
        print("created timer")
    
    def check_time_expired(self):
        now = maya.now().datetime()
        MINUTES = 35
        actual_difference = (self.match_time - now).total_seconds()
        ping_time_difference = actual_difference - (MINUTES * 60)
        # check if actual difference is in the future
        print( f"Pinging for  {self} in : {ping_time_difference} seconds" )

        # ping immediately if time is in the past
        if (ping_time_difference < 0):
            print("calling callback")
            # give discord time to finish actions before calling callback
            time.sleep(5)
            self.on_match_end(self)
            return True

        return False

    def exec_every_n_seconds(self, n, f, args):
        print(locals())
        stop_periodic = False
        first_called = datetime.now()
        stop_periodic = f()
        num_calls=1
        drift = timedelta()
        time_period = timedelta(seconds=n)
        while 1:
            if (self.stop == True) or (stop_periodic == True) or (self.fire == False):
                return
            time.sleep(n-drift.microseconds/1000000.0)
            current_time = datetime.now()
            stop_periodic = f()
            num_calls += 1
            difference = current_time - first_called
            drift = difference - time_period * num_calls

    def show_match_time(self):
        print(self.get_match_string())


    def get_match_string(self):
        time_string = self.match_time.strftime("%A %d/%m @ %H:%M")
        return ("Match ID#{1} [{0}] - " + time_string).format(self.opponent_name, self.id)

    def get_match_conf(self):
        return f"[{self.id}] [{self.messageid}] {self.opponent_name}, {self.absolute_time}"

    def cancel(self):
        print("set fire to false")
        self.fire = False

    def is_cancelled(self):
        print("check if cancelled")
        print(f"{not self.fire}")
        return not self.fire
    
    def stop(self):
        print("stopping thread")
        self.stop = True

    def parse_time(self):
        match_time = maya.when("today").datetime
        try:
            match_time = maya.when(self.raw_time, prefer_dates_from="future").datetime(to_timezone='Europe/London', naive=False)
        except ValueError:
            print("failed to parse relative time. trying \"absolute\" time")
            try:
                match_time = maya.parse(self.raw_time, day_first=True).datetime(to_timezone='Europe/London', naive=False)
            except ValueError:
                print("not absolute time")
        
        return match_time


