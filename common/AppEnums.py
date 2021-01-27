from enum import Enum


class StackStatus(Enum):
    DONE = 1
    STOPPED = 2
    FAILURE = 3
    INPROGRESS = 4

    @staticmethod
    def getString(status):
        return {
            StackStatus.DONE.value: "DONE",
            StackStatus.FAILURE.value: "FAILURE",
            StackStatus.INPROGRESS.value: "INPROGRESS",
            StackStatus.STOPPED.value: "STOPPED"
        }[status]

class Resources(Enum):
    USED = 1
    FREE = 0

    @staticmethod
    def getString(status):
        return {
            Resources.USED.value: "USED",
            Resources.FREE.value: "FREE",
        }[status]

class ClusterRole(Enum):
    MASTER = 1
    WORKER = 0

    @staticmethod
    def getString(status):
        return {
            ClusterRole.MASTER.value: "MASTER",
            ClusterRole.WORKER.value: "WORKER",
        }[status]


