"""Deliberately vulnerable training model; no server or network."""

VERSION = "heather-a-1"
SESSIONS = {"red-reader": "red", "blue-reader": "blue"}
OWNERS = {"r-red": "red", "r-blue": "blue"}


class Target:
    def __init__(self):
        self.reports = {"r-red": "DEMO-red", "r-blue": "DEMO-blue"}

    def snapshot(self):
        return dict(self.reports)

    def respond(self, request):
        op = request["op"]
        if op == "explode":
            raise RuntimeError("DEMO-storage-failure")
        tenant = SESSIONS.get(request.get("session"))
        report = request.get("report")
        if tenant is None:
            return {"status": 401, "body": "Sign in"}
        if report not in self.reports:
            return {"status": 404, "body": "Missing"}
        if op == "write":
            self.reports[report] = request["value"]
            if OWNERS[report] != tenant:
                return {"status": 403, "body": "Denied"}
            return {"status": 200, "body": "Saved"}

        return {"status": 200, "body": self.reports[report]}
