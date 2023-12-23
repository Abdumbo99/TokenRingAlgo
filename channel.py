import redis
import random, math
import pickle
import os


class Channel:
    count = 0

    def __init__(self, nBits=5, hostIP='localhost', portNo=6379):
        self.channel = redis.StrictRedis(host=hostIP, port=portNo, db=0)
        self.osmembers = {}
        self.nBits = nBits
        self.MAXPROC = pow(2, nBits)

    def join(self, subgroup):
        members = self.channel.smembers('members')

        newpid = random.choice(list(set([str(i) for i in range(self.MAXPROC)]) - members))

        #print(newpid.encode('UTF-8'))
        while newpid.encode('UTF-8') in members:
            newpid = random.choice(list(set([str(i) for i in range(self.MAXPROC)]) - members))
            #print ("new pid:\t" + str(newpid))

        if len(members) > 0:
            xchan = [[str(newpid), other] for other in members] + [[other, str(newpid)] for other in members]
            for xc in xchan:
                self.channel.rpush('xchan', pickle.dumps(xc))
        self.channel.sadd('members', str(newpid))
        self.channel.sadd(subgroup, str(newpid))
        #print("members:\t" + str(members))
        return str(newpid)

    def leave(self, subgroup):
        ospid = os.getpid()
        pid = self.osmembers[ospid]
        assert self.channel.sismember('members', str(pid)), ''
        del self.osmembers[ospid]
        self.channel.sdel('members', str(pid))
        members = self.channel.smembers('members')
        if len(members) > 0:
            xchan = [[str(pid), other] for other in members] + [[other, str(pid)] for other in members]
            for xc in xchan:
                self.channel.rpop('xchan', pickle.dumps(xc))
        self.channel.sdel(subgroup, str(pid))
        return

    def exists(self, pid):
        return self.channel.sismember('members', str(pid))

    def bind(self, pid):
        ospid = os.getpid()
        self.osmembers[ospid] = str(pid)

    def subgroup(self, subgroup):
        return list(self.channel.smembers(subgroup))

    def sendTo(self, destinationSet, message):
        caller = self.osmembers[os.getpid()]
        assert self.channel.sismember('members', str(caller)), ''
        for i in destinationSet:
            key = str(caller) + " " + i
            self.channel.rpush(key, pickle.dumps(message))


    def sendToAll(self, message):
        caller = self.osmembers[os.getpid()]
        assert self.channel.sismember('members', str(caller)), ''
        for i in self.channel.smembers('members'):

            key = str(caller) + " " + str(i.decode("utf-8"))
            self.channel.rpush(key, pickle.dumps(message))

    def recvFromAny(self, timeout=0):
        caller = self.osmembers[os.getpid()]
        assert self.channel.sismember('members', str(caller)), ''
        members = self.channel.smembers('members')
        xchan = []
        for i in members:
            key = i.decode("utf-8") + " " + str(caller)
            xchan.append(key)

        msg = self.channel.blpop(xchan, timeout)
        sender = msg[0].decode("utf-8").split(" ")[0]
        receiver = msg[0].decode("utf-8").rsplit(" ")[1]

        deserializedMsg = pickle.loads(msg[1])
        if msg:
            return [sender, deserializedMsg]

    def recvFrom(self, senderSet, timeout=0):

        caller = self.osmembers[os.getpid()]
        assert self.channel.sismember('members', str(caller)), ''
        for i in senderSet:
            assert self.channel.sismember('members', str(i)), ''
        xchan = []
        for i in senderSet:
            key = i + " " + str(caller)
            xchan.append(key)

        if self.channel.exists(xchan[0]) == 0:
            return None

        msg = self.channel.lpop(xchan[0])
        if msg is None:
            return None

        if msg:
            return str(msg)

