# cython: language_level=3
import pyperf
cimport cython

# Task IDs
cdef int I_IDLE = 1
cdef int I_WORK = 2
cdef int I_HANDLERA = 3
cdef int I_HANDLERB = 4
cdef int I_DEVA = 5
cdef int I_DEVB = 6

# Packet types
cdef int K_DEV = 1000
cdef int K_WORK = 1001

# Packet
cdef int BUFSIZE = 4
BUFSIZE_RANGE = range(BUFSIZE)

cdef class Packet:
    cdef public object link
    cdef public int ident
    cdef public int kind
    cdef public int datum
    cdef public list data

    def __init__(self, l, int i, int k):
        self.link = l
        self.ident = i
        self.kind = k
        self.datum = 0
        self.data = [0] * BUFSIZE

    cdef object append_to(self, object lst):
        self.link = None
        if lst is None:
            return self
        else:
            cdef object p = lst
            cdef object next_p = p.link
            while next_p is not None:
                p = next_p
                next_p = p.link
            p.link = self
            return lst

# Task Records
cdef class TaskRec:
    pass

cdef class DeviceTaskRec(TaskRec):
    cdef public object pending

    def __init__(self):
        self.pending = None

cdef class IdleTaskRec(TaskRec):
    cdef public int control
    cdef public int count

    def __init__(self):
        self.control = 1
        self.count = 10000

cdef class HandlerTaskRec(TaskRec):
    cdef public object work_in
    cdef public object device_in

    def __init__(self):
        self.work_in = None
        self.device_in = None

    cdef object workInAdd(self, Packet p):
        self.work_in = p.append_to(self.work_in)
        return self.work_in

    cdef object deviceInAdd(self, Packet p):
        self.device_in = p.append_to(self.device_in)
        return self.device_in

cdef class WorkerTaskRec(TaskRec):
    cdef public int destination
    cdef public int count

    def __init__(self):
        self.destination = I_HANDLERA
        self.count = 0

# Task
cdef class TaskState:
    cdef public bint packet_pending
    cdef public bint task_waiting
    cdef public bint task_holding

    def __init__(self):
        self.packet_pending = True
        self.task_waiting = False
        self.task_holding = False

    cdef object packetPending(self):
        self.packet_pending = True
        self.task_waiting = False
        self.task_holding = False
        return self

    cdef object waiting(self):
        self.packet_pending = False
        self.task_waiting = True
        self.task_holding = False
        return self

    cdef object running(self):
        self.packet_pending = False
        self.task_waiting = False
        self.task_holding = False
        return self

    cdef object waitingWithPacket(self):
        self.packet_pending = True
        self.task_waiting = True
        self.task_holding = False
        return self

    cdef bint isPacketPending(self):
        return self.packet_pending

    cdef bint isTaskWaiting(self):
        return self.task_waiting

    cdef bint isTaskHolding(self):
        return self.task_holding

    cdef bint isTaskHoldingOrWaiting(self):
        return self.task_holding or (not self.packet_pending and self.task_waiting)

    cdef bint isWaitingWithPacket(self):
        return self.packet_pending and self.task_waiting and not self.task_holding

cdef bint tracing = False
cdef int layout = 0

def trace(a):
    global layout
    layout -= 1
    if layout <= 0:
        print()
        layout = 50
    print(a, end='')

cdef int TASKTABSIZE = 10

cdef class TaskWorkArea:
    cdef public list taskTab
    cdef public object taskList
    cdef public int holdCount
    cdef public int qpktCount

    def __init__(self):
        self.taskTab = [None] * TASKTABSIZE
        self.taskList = None
        self.holdCount = 0
        self.qpktCount = 0

cdef TaskWorkArea taskWorkArea = TaskWorkArea()

cdef class Task(TaskState):
    cdef public object link
    cdef public int ident
    cdef public int priority
    cdef public object input
    cdef public object handle

    def __init__(self, int i, int p, object w, TaskState initialState, object r):
        self.link = taskWorkArea.taskList
        self.ident = i
        self.priority = p
        self.input = w

        self.packet_pending = initialState.isPacketPending()
        self.task_waiting = initialState.isTaskWaiting()
        self.task_holding = initialState.isTaskHolding()

        self.handle = r

        taskWorkArea.taskList = self
        taskWorkArea.taskTab[i] = self

    cdef object fn(self, object pkt, object r):
        raise NotImplementedError

    cdef object addPacket(self, Packet p, object old):
        if self.input is None:
            self.input = p
            self.packet_pending = True
            if self.priority > old.priority:
                return self
        else:
            p.append_to(self.input)
        return old

    cdef object runTask(self):
        cdef object msg
        if self.isWaitingWithPacket():
            msg = self.input
            self.input = msg.link
            if self.input is None:
                self.running()
            else:
                self.packetPending()
        else:
            msg = None

        return self.fn(msg, self.handle)

    cdef object waitTask(self):
        self.task_waiting = True
        return self

    cdef object hold(self):
        taskWorkArea.holdCount += 1
        self.task_holding = True
        return self.link

    cdef object release(self, int i):
        cdef object t = self.findtcb(i)
        t.task_holding = False
        if t.priority > self.priority:
            return t
        else:
            return self

    cdef object qpkt(self, Packet pkt):
        cdef object t = self.findtcb(pkt.ident)
        taskWorkArea.qpktCount += 1
        pkt.link = None
        pkt.ident = self.ident
        return t.addPacket(pkt, self)

    cdef object findtcb(self, int id):
        cdef object t = taskWorkArea.taskTab[id]
        if t is None:
            raise Exception("Bad task id %d" % id)
        return t

# Specific task implementations
cdef class DeviceTask(Task):
    def __init__(self, int i, int p, object w, TaskState s, object r):
        Task.__init__(self, i, p, w, s, r)

    cdef object fn(self, object pkt, object r):
        cdef DeviceTaskRec d = r
        if pkt is None:
            pkt = d.pending
            if pkt is None:
                return self.waitTask()
            else:
                d.pending = None
                return self.qpkt(pkt)
        else:
            d.pending = pkt
            if tracing:
                trace(pkt.datum)
            return self.hold()

cdef class HandlerTask(Task):
    def __init__(self, int i, int p, object w, TaskState s, object r):
        Task.__init__(self, i, p, w, s, r)

    cdef object fn(self, object pkt, object r):
        cdef HandlerTaskRec h = r
        cdef object work, dev
        cdef int count
        
        if pkt is not None:
            if pkt.kind == K_WORK:
                h.workInAdd(pkt)
            else:
                h.deviceInAdd(pkt)
        work = h.work_in
        if work is None:
            return self.waitTask()
        count = work.datum
        if count >= BUFSIZE:
            h.work_in = work.link
            return self.qpkt(work)

        dev = h.device_in
        if dev is None:
            return self.waitTask()

        h.device_in = dev.link
        dev.datum = work.data[count]
        work.datum = count + 1
        return self.qpkt(dev)

cdef class IdleTask(Task):
    def __init__(self, int i, int p, object w, TaskState s, object r):
        Task.__init__(self, i, 0, None, s, r)

    cdef object fn(self, object pkt, object r):
        cdef IdleTaskRec i_rec = r
        i_rec.count -= 1
        if i_rec.count == 0:
            return self.hold()
        elif i_rec.control & 1 == 0:
            i_rec.control //= 2
            return self.release(I_DEVA)
        else:
            i_rec.control = i_rec.control // 2 ^ 0xd008
            return self.release(I_DEVB)

cdef int A = ord('A')

cdef class WorkTask(Task):
    def __init__(self, int i, int p, object w, TaskState s, object r):
        Task.__init__(self, i, p, w, s, r)

    cdef object fn(self, object pkt, object r):
        cdef WorkerTaskRec w_rec = r
        cdef int dest, i
        
        if pkt is None:
            return self.waitTask()

        if w_rec.destination == I_HANDLERA:
            dest = I_HANDLERB
        else:
            dest = I_HANDLERA

        w_rec.destination = dest
        pkt.ident = dest
        pkt.datum = 0

        for i in BUFSIZE_RANGE:
            w_rec.count += 1
            if w_rec.count > 26:
                w_rec.count = 1
            pkt.data[i] = A + w_rec.count - 1

        return self.qpkt(pkt)

cdef void schedule():
    cdef object t = taskWorkArea.taskList
    while t is not None:
        if tracing:
            print("tcb =", t.ident)

        if t.isTaskHoldingOrWaiting():
            t = t.link
        else:
            if tracing:
                trace(chr(ord("0") + t.ident))
            t = t.runTask()

cdef class Richards:
    cdef bint run_cython(self, int iterations):
        cdef int i
        cdef object wkq
        
        for i in range(iterations):
            taskWorkArea.holdCount = 0
            taskWorkArea.qpktCount = 0

            IdleTask(I_IDLE, 1, 10000, TaskState().running(), IdleTaskRec())

            wkq = Packet(None, 0, K_WORK)
            wkq = Packet(wkq, 0, K_WORK)
            WorkTask(I_WORK, 1000, wkq, TaskState().waitingWithPacket(), WorkerTaskRec())

            wkq = Packet(None, I_DEVA, K_DEV)
            wkq = Packet(wkq, I_DEVA, K_DEV)
            wkq = Packet(wkq, I_DEVA, K_DEV)
            HandlerTask(I_HANDLERA, 2000, wkq, TaskState().waitingWithPacket(), HandlerTaskRec())

            wkq = Packet(None, I_DEVB, K_DEV)
            wkq = Packet(wkq, I_DEVB, K_DEV)
            wkq = Packet(wkq, I_DEVB, K_DEV)
            HandlerTask(I_HANDLERB, 3000, wkq, TaskState().waitingWithPacket(), HandlerTaskRec())

            wkq = None
            DeviceTask(I_DEVA, 4000, wkq, TaskState().waiting(), DeviceTaskRec())
            DeviceTask(I_DEVB, 5000, wkq, TaskState().waiting(), DeviceTaskRec())

            schedule()

            if taskWorkArea.holdCount == 9297 and taskWorkArea.qpktCount == 23246:
                pass
            else:
                return False

        return True

    def run(self, iterations):
        return self.run_cython(iterations)

if __name__ == "__main__":
    runner = pyperf.Runner()
    runner.metadata['description'] = "The Richards benchmark"

    richard = Richards()
    runner.bench_func('richards', richard.run, 1)